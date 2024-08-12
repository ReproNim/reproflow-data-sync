#!/usr/bin/env python3

import getpass
import os
import sys
from itertools import chain
from pathlib import Path

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import jsonlines
import pandas as pd

import click
import logging

from repronim_timing import (TMapService, Clock,
                             generate_id, dump_jsonl,
                             get_session_id, get_tmap_svc)
from repronim_dumps import MarkRecord

# initialize the logger
# Note: all logs goes to stderr
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)
#logger.debug(f"name={__name__}")


# Define abstract series model
class SeriesData(BaseModel):
    lst: Optional[List] = Field([], description="List JSONL object "
                                                "in series")
    name: Optional[str] = Field(None, description="Series name")
    count: Optional[int] = Field(0, description="Number of object in series")
    swimlane: Optional[object] = Field(None, description="Swimlane model reference")
    isotime_start: Optional[datetime] = Field(None, description="Series start "
                                                                "datetime")
    isotime_end: Optional[datetime] = Field(None, description="Series end "
                                                                "datetime w/o "
                                                              "last item")
    interval: Optional[float] = Field(0.0, description="Series interval "
                                                       "in seconds")
    duration: Optional[float] = Field(0.0, description="Series duration w/o last "
                                                       "item at this moment")
    next_series_interval: Optional[float] = Field(0.0,
                                    description="Interval to next series if any in seconds, "
                                                "otherwise 0.0. Claculated as"
                                                "start-start interval between series")


# Define swimlane object model
class SwimlaneModel(BaseModel):
    name: Optional[str] = Field(None, description="Swimlane name")
    clock: Optional[Clock] = Field(None, description="Clock model")
    isotime_field: Optional[str] = Field(None, description="Field name for item in "
                                                           "swimlane containing "
                                                           "datetime in isotime format")
    data: Optional[List] = Field([], description="List of data object "
                                                 "from JSONL")
    series: Optional[List[SeriesData]] = Field([], description="List of detected series "
                                                               "for the swimlane")


# Define dump model
class DumpModel(BaseModel):
    session_id: Optional[str] = Field(None,
                                      description="Unique session identifier")
    birch: Optional[SwimlaneModel] = Field(SwimlaneModel(name="birch",
                                                         clock=Clock.BIRCH,
                                                         isotime_field="isotime"),
                                           description="Birch swimlane")
    dicoms: Optional[SwimlaneModel] = Field(SwimlaneModel(name="dicoms",
                                                          clock=Clock.DICOMS,
                                                          isotime_field="acquisition_isotime"),
                                            description="DICOMs swimlane")
    psychopy: Optional[SwimlaneModel] = Field(SwimlaneModel(name="psychopy",
                                                            clock=Clock.PSYCHOPY,
                                                            isotime_field="isotime"),
                                              description="PsychoPy swimlane")
    qrinfo: Optional[SwimlaneModel] = Field(SwimlaneModel(name="qrinfo",
                                                          clock=Clock.QRINFO,
                                                          isotime_field="isotime_start"),
                                            description="QRInfo swimlane")
    map_by_id: Optional[dict] = Field({}, description="Map of all objects by "
                                                      "unique ID")

    @property
    def swimlanes(self) -> List[SwimlaneModel]:
        return [self.dicoms, self.birch, self.qrinfo, self.psychopy]

    def get_by_id(self, uid: str):
        return self.map_by_id.get(uid)


def parse_isotime(v: str) -> datetime:
    if not v:
        return None
    ts = pd.to_datetime(v)
    if ts.tzinfo is not None:
        ts = ts.tz_convert('America/New_York')
    isotime = ts.tz_localize(None)
    return isotime


# calculate interval between first and last dicom in series if
# series has more than 1 dicoms
def calc_dicoms_series_interval(series: List) -> float:
    # calculate interval between first and last dicom in series
    if series and len(series) > 1:
        t1 = parse_isotime(series[0].get('acquisition_isotime'))
        t2 = parse_isotime(series[-1].get('acquisition_isotime'))
        return (t2-t1).total_seconds() / (len(series)-1)
    logger.debug(f"Series {series} has less than 2 dicoms")
    return 2.0


# Find birch series based on DICOMs series interval
def find_swimlane_series(swimlane: SwimlaneModel,
                         interval: float) -> List[SeriesData]:
    lst: List[SeriesData] = []
    dt_min:float = interval * 0.8
    dt_max:float = interval * 1.2

    last_isotime: datetime = None
    objs: List = []
    for obj in chain(swimlane.data, [swimlane.data[0]]):
        isotime: datetime = parse_isotime(obj.get(swimlane.isotime_field))
        if len(objs) == 0:
            objs.append(obj)
            last_isotime = isotime
            continue

        dt: float = (isotime - last_isotime).total_seconds()
        if dt_min <= dt <= dt_max:
            objs.append(obj)
        else:
            # consider only more than 5 objects in series
            if len(objs) > 5:
                sd: SeriesData = SeriesData()
                sd.swimlane = swimlane
                sd.lst = objs
                sd.count = len(objs)
                sd.name = f"{swimlane.name}-series-{(len(lst)+1)}"
                sd.isotime_start = parse_isotime(objs[0].get(swimlane.isotime_field))
                sd.isotime_end = parse_isotime(objs[-1].get(swimlane.isotime_field))
                sd.interval = (last_isotime - sd.isotime_start).total_seconds() / (sd.count-1)
                sd.next_series_interval = 0
                sd.duration = (sd.isotime_end - sd.isotime_start).total_seconds()
                if len(lst) > 0:
                    lst[-1].next_series_interval = (
                        (sd.isotime_start - lst[-1].isotime_start).total_seconds())
                lst.append(sd)
            else:
                logger.debug(f"Skip {swimlane.name} series (too small={len(objs)}): {objs}")
            objs = []
            objs.append(obj)

        last_isotime = isotime

    return lst


# Return list of list DICOMs object in each series
def find_dicoms_func_series(model: DumpModel) -> List[SeriesData]:
    df = pd.DataFrame(model.dicoms.data)
    # filter by type, study and series
    filtered_df = df[
        (df['type'] == 'DicomRecord') &
        (df['study'] == 'dbic^QA') &
        (df['series'].str.startswith('func-'))
        ]

    # group by series
    grouped_df = filtered_df.groupby('series')

    lst: List = []
    last_sd: SeriesData = None
    for series, group in grouped_df:
        sd: SeriesData = SeriesData()
        sd.swimlane = model.dicoms
        sd.lst = [model.get_by_id(uid) for uid in group['id']]
        sd.count = len(sd.lst)
        sd.name = series
        sd.isotime_start = parse_isotime(
            sd.lst[0].get('acquisition_isotime'))
        sd.isotime_end = parse_isotime(
            sd.lst[-1].get('acquisition_isotime'))
        sd.interval = calc_dicoms_series_interval(sd.lst)
        sd.next_series_interval = 0.0
        sd.duration = (sd.isotime_end -
                       sd.isotime_start).total_seconds()
        if last_sd:
            last_sd.next_series_interval = (
                (sd.isotime_start - last_sd.isotime_start).total_seconds())
        lst.append(sd)
        last_sd = sd
    return lst


# match SeriesData object with another one
def match_series_data(sd1: SeriesData, sd2: SeriesData) -> bool:
    #if sd1.name == 'func-bold_task-rest_run-2' and sd2.name == 'birch-series-1':
    #    logger.debug(f"Match: {sd1} with {sd2}")

    if not sd1 or not sd2:
        return False

    # match item count
    if sd1.count != sd2.count:
        return False

    # match interval corresponds to each other
    if sd1.interval and sd2.interval:
        t_min: float = sd1.interval * 0.95
        t_max: float = sd1.interval * 1.05
        if not (t_min <= sd2.interval <= t_max):
            return False

    # match inter series interval matches as well
    if sd1.next_series_interval and sd2.next_series_interval:
        t_min: float = sd1.next_series_interval * 0.95
        t_max: float = sd1.next_series_interval * 1.05
        if not (t_min <= sd2.next_series_interval <= t_max):
            return False
    else:
        return False
    return True



def parse_jsonl(path: str) -> List:
    # Load JSONL file
    lst = []
    with jsonlines.open(path) as reader:
        for obj in reader:
            lst.append(obj)
    return lst


def build_model(session_id: str, path: str) -> DumpModel:
    m: DumpModel = DumpModel()
    m.session_id = session_id
    # first, load all JSONL data to memory
    m.dicoms.data = parse_jsonl(os.path.join(path, 'dump_dicoms.jsonl'))
    m.birch.data = parse_jsonl(os.path.join(path, 'dump_birch.jsonl'))
    m.psychopy.data = parse_jsonl(os.path.join(path, 'dump_psychopy.jsonl'))
    m.qrinfo.data = parse_jsonl(os.path.join(path, 'dump_qrinfo.jsonl'))
    for obj in chain(m.dicoms.data, m.birch.data,
                     m.psychopy.data, m.qrinfo.data):
        #logger.debug(f"Object: {obj}")
        m.map_by_id[obj.get('id')] = obj

    # as second, detect possible series in each swimlane
    m.dicoms.series = find_dicoms_func_series(m)
    m.birch.series = find_swimlane_series(m.birch,
                                          m.dicoms.series[0].interval)
    m.qrinfo.series = find_swimlane_series(m.qrinfo,
                                           m.dicoms.series[0].interval)
    m.psychopy.series = find_swimlane_series(m.psychopy,
                                             m.dicoms.series[0].interval)

    # dump short series info
    for sl in m.swimlanes:
        logger.debug(f"Swimlane: {sl.name}")
        logger.debug(f"  Found {len(sl.series)} {sl.name} series")
        for sd in sl.series:
            logger.debug(f"  Series: {sd.name}, "
                         f"count: {sd.count}, "
                         f"interval: {sd.interval}, "
                         f"next_series_interval: {sd.next_series_interval}, "
                         f"ids: {sd.lst[0].get('id')}..{sd.lst[-1].get('id')}")

    # dump long series info and data
    for sl in m.swimlanes:
        for sd in sl.series:
            logger.debug(f"{sl.name}.{sd.name} : {sd.lst}")

    return m


def generate_marks(model: DumpModel):

    marks: List[MarkRecord] = []
    offset: dict = {}
    for dicoms_sd in model.dicoms.series:
        # generate start mark
        mark: MarkRecord = MarkRecord()
        mark.id = generate_id('mark')
        mark.session_id = model.session_id
        mark.kind = "Func series start"
        mark.name = f"{dicoms_sd.name}_start"
        mark.target_ids.append(dicoms_sd.lst[0].get('id'))
        mark.dicoms_isotime = dicoms_sd.isotime_start
        mark.dicoms_duration = dicoms_sd.duration

        # try to match series
        map_series: dict = {}
        for swiml in [model.birch, model.qrinfo, model.psychopy]:
            for ser_sd in swiml.series:
                # TODO: in future also consider match algorithm based on
                #       existing table table for previous series
                if match_series_data(dicoms_sd, ser_sd):
                    map_series[swiml.name] = ser_sd
                    mark.target_ids.append(ser_sd.lst[0].get('id'))
                    setattr(mark, f"{swiml.name}_isotime", ser_sd.isotime_start)
                    setattr(mark, f"{swiml.name}_duration", ser_sd.duration)
                    offset[ser_sd.name] = (dicoms_sd.isotime_start -
                                           ser_sd.isotime_start).total_seconds()
                    break

        marks.append(mark)
        logger.debug(f"{mark.model_dump_json()}")
        # dump_jsonl(mark)

        # generate marks for each scan in series
        for i in range(len(dicoms_sd.lst)):
            mark = MarkRecord()
            mark.id = generate_id('mark')
            mark.session_id = model.session_id
            mark.kind = "Func series scan"
            mark.name = f"{dicoms_sd.name}_scan_{i}"
            mark.target_ids.append(dicoms_sd.lst[i].get('id'))
            mark.dicoms_isotime = parse_isotime(
                dicoms_sd.lst[i].get(
                    model.dicoms.isotime_field))
            #mark.dicoms_duration = None
            for k, v in map_series.items():
                mark.target_ids.append(v.lst[i].get('id'))
                setattr(mark, f"{k}_isotime", parse_isotime(
                    v.lst[i].get(v.swimlane.isotime_field)))
                #setattr(mark, f"{k}_duration", None)
            marks.append(mark)
            logger.debug(f"{mark.model_dump_json()}")
            # dump_jsonl(mark)

        # generate end mark
        mark = MarkRecord()
        mark.id = generate_id('mark')
        mark.session_id = model.session_id
        mark.kind = "Func series end"
        mark.name = f"{dicoms_sd.name}_end"
        mark.target_ids.append(dicoms_sd.lst[-1].get('id'))
        mark.dicoms_isotime = dicoms_sd.isotime_end
        #mark.dicoms_duration = None
        logger.debug(f"Mark: {mark}")
        for k, v in map_series.items():
            mark.target_ids.append(v.lst[-1].get('id'))
            setattr(mark, f"{k}_isotime", v.isotime_end)
            #setattr(mark, f"{k}_duration", None)
        marks.append(mark)
        logger.debug(f"{mark.model_dump_json()}")
        # dump_jsonl(mark)

    logger.debug(f"Dicoms offsets: {offset}")
    logger.debug(f"Generated marks after pass 1, done: {marks}")

    # try to match marks with existing tmap also
    # TODO: in future consider also to use tmap record from
    #  mark generator if any found
    logger.debug("Try to match marks with tmap service")
    for mark in marks:
        dicoms_isotime: datetime = mark.dicoms_isotime
        dicoms_id: str = mark.target_ids[0]
        for swiml in [model.birch, model.qrinfo, model.psychopy]:
            for ser_sd in swiml.series:
                for obj in ser_sd.lst:
                    obj_id: str = obj.get('id')
                    isotime_1: datetime = parse_isotime(
                        obj.get(swiml.isotime_field))

                    isotime_2: datetime = get_tmap_svc().convert(
                        model.dicoms.clock, swiml.clock,
                        dicoms_isotime)

                    dt: float = (isotime_1 - isotime_2).total_seconds()

                    threshold: float = 0.9
                    logger.debug(f"{dicoms_id}/{obj_id}=, dt={dt}")
                    if (-threshold <= dt <= threshold and
                            obj_id not in mark.target_ids):
                        logger.debug(f"Time matched : {mark.name}")
                        logger.debug(f"             : {dt} sec, ({isotime_1} - {isotime_2})")
                        logger.debug(f"             : {dicoms_id} = {dicoms_isotime}")
                        logger.debug(f"             : {obj_id} = {isotime_2}")
                        mark.target_ids.append(obj_id)
                        logger.debug(f"             : set {swiml.name}_isotime = {isotime_1}")
                        setattr(mark, f"{swiml.name}_isotime", isotime_1)
                        if mark.kind == "Func series start":
                            logger.debug(f"             : set {swiml.name}_duration = {ser_sd.duration}")
                            setattr(mark, f"{swiml.name}_duration", ser_sd.duration)
                        # break next items
                        continue

    logger.debug("Done match marks with tmap service")
    logger.debug(f"Generated marks after pass 2, done: {marks}")


    # now dump all to stdout
    for mark in marks:
        dump_jsonl(mark)




@click.command(help='Dump calculated timing synchronization marks info.')
@click.argument('path', type=click.Path(exists=True))
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level')
@click.pass_context
def main(ctx, path: str, log_level):
    logger.setLevel(log_level)
    logger.debug("dump_marks.py tool")
    logger.info(f"Started on    : {datetime.now()}, {getpass.getuser()}@{os.uname().nodename}")
    logger.debug(f"Working dir   : {os.getcwd()}")
    logger.info(f"Session path  : {path}")

    session_id: str = get_session_id(path)
    logger.info(f"Session ID    : {session_id}")

    if not os.path.exists(path):
        logger.error(f"Session path does not exist: {path}")
        return 1

    path_dumps: str = os.path.join(path, "timing-dumps")
    if not os.path.exists(path_dumps):
        logger.error(f"Session timing-dumps path does not exist: {path_dumps}")
        return 1

    # load tmap service
    _tmp_svc = get_tmap_svc()

    model: DumpModel = build_model(session_id, path_dumps)
    #logger.debug(f"Model: {model}")

    generate_marks(model)
    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)