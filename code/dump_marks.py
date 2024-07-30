#!/usr/bin/env python3

import getpass
import os
import sys
from itertools import chain

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import jsonlines
import pandas as pd

import click
import logging


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
    data: Optional[List] = Field([], description="List of data object "
                                                 "from JSONL")
    series: Optional[List[SeriesData]] = Field([], description="List of detected series "
                                                               "for the swimlane")


# Define dump model
class DumpModel(BaseModel):
    birch: Optional[SwimlaneModel] = Field(SwimlaneModel(name="birch"),
                                           description="Birch swimlane")
    dicoms: Optional[SwimlaneModel] = Field(SwimlaneModel(name="dicoms"),
                                            description="DICOMs swimlane")
    psychopy: Optional[SwimlaneModel] = Field(SwimlaneModel(name="psychopy"),
                                              description="PsychoPy swimlane")
    qrinfo: Optional[SwimlaneModel] = Field(SwimlaneModel(name="qrinfo"),
                                            description="QRInfo swimlane")
    map_by_id: Optional[dict] = Field({}, description="Map of all objects by "
                                                      "unique ID")

    @property
    def swimlanes(self) -> List[SwimlaneModel]:
        return [self.dicoms, self.birch, self.qrinfo, self.psychopy]

    def get_by_id(self, uid: str):
        return self.map_by_id.get(uid)



# Define synchronization mark/tag model
class MarkRecord(BaseModel):
    type: Optional[str] = Field("MarkRecord", description="JSON record type/class")
    id: Optional[str] = Field(None, description="Mark object unique ID")
    kind: Optional[str] = Field(None, description="Mark kind/type")
    name: Optional[str] = Field(None, description="Mark name")
    target_ids: Optional[List[str]] = Field([], description="List of unique "
                                                        "series in seconds")
    dicoms_isotime: Optional[str] = Field(None, description="DICOMs acquisition "
                                                            "time in ISO format")
    dicoms_duration: Optional[float] = Field(None, description="DICOMs series duration "
                                                               "in seconds")
    birch_isotime: Optional[str] = Field(None, description="Birch acquisition "
                                                           "time in ISO format")
    birch_duration: Optional[float] = Field(None, description="Birch series duration "
                                                              "in seconds")
    qrinfo_isotime: Optional[str] = Field(None, description="QRInfo acquisition "
                                                            "time in ISO format")
    qrinfo_duration: Optional[float] = Field(None, description="QRInfo series duration "
                                                               "in seconds")
    psychopy_isotime: Optional[str] = Field(None, description="PsychoPy acquisition "
                                                             "time in ISO format")
    psychopy_duration: Optional[float] = Field(None, description="Psychopy series duration "
                                                                "in seconds")



last_id: dict = { "mark": 0 }
def generate_id(name: str) -> str:
    # generate unique id based on int sequence
    global last_id
    last_id[name] += 1
    return f"{name}_{last_id[name]:06d}"


def parse_isotime(v: str) -> datetime:
    if not v:
        return None
    ts = pd.to_datetime(v)
    if ts.tzinfo is not None:
        ts = ts.tz_convert('America/New_York')
    isotime = ts.tz_localize(None)
    return isotime


def dump_jsonl(obj):
    print(obj.json())

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
                         isotime_filed: str,
                         interval: float) -> List[SeriesData]:
    lst: List[SeriesData] = []
    dt_min:float = interval * 0.8
    dt_max:float = interval * 1.2

    last_isotime: datetime = None
    objs: List = []
    for obj in chain(swimlane.data, [swimlane.data[0]]):
        isotime: datetime = parse_isotime(obj.get(isotime_filed))
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
                sd.lst = objs
                sd.count = len(objs)
                sd.name = f"{swimlane.name}-series-{(len(lst)+1)}"
                sd.isotime_start = parse_isotime(objs[0].get(isotime_filed))
                sd.isotime_end = parse_isotime(objs[-1].get(isotime_filed))
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


def build_model(path: str) -> DumpModel:
    m: DumpModel = DumpModel()
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
    m.birch.series = find_swimlane_series(m.birch, 'isotime',
                                          m.dicoms.series[0].interval)
    m.qrinfo.series = find_swimlane_series(m.qrinfo, 'isotime_start',
                                           m.dicoms.series[0].interval)
    m.psychopy.series = find_swimlane_series(m.psychopy, 'isotime',
                                             m.dicoms.series[0].interval)

    # dump short series info
    for sl in m.swimlanes:
        logger.debug(f"Swimlane: {sl.name}")
        logger.debug(f"  Found {len(sl.series)} {sl.name} series")
        for sd in sl.series:
            logger.debug(f"  Series: {sd.name}, "
                         f"count: {sd.count}, "
                         f"interval: {sd.interval}, "
                         f"next_series_interval: {sd.next_series_interval}")

    # dump long series info and data
    for sl in m.swimlanes:
        for sd in sl.series:
            logger.debug(f"{sl.name}.{sd.name} : {sd.lst}")

    return m


def generate_marks(model: DumpModel):

    offset: dict = {}
    for dicoms_sd in model.dicoms.series:
        #logger.debug(f"DICOMs series: {sd}")
        mark: MarkRecord = MarkRecord()
        mark.id = generate_id('mark')
        mark.kind = "Func series start"
        mark.name = f"{dicoms_sd.name}_start"
        mark.target_ids.append(dicoms_sd.lst[0].get('id'))
        mark.dicoms_isotime = dicoms_sd.isotime_start.isoformat()
        mark.dicoms_duration = dicoms_sd.duration

        # try to match series
        for ser in [model.birch, model.qrinfo, model.psychopy]:
            for ser_sd in ser.series:
                if match_series_data(dicoms_sd, ser_sd):
                    mark.target_ids.append(ser_sd.lst[0].get('id'))
                    setattr(mark, f"{ser.name}_isotime", ser_sd.isotime_start.isoformat())
                    setattr(mark, f"{ser.name}_duration", ser_sd.duration)
                    offset[ser_sd.name] = (dicoms_sd.isotime_start -
                                           ser_sd.isotime_start).total_seconds()
                    break

        logger.debug(f"Mark: {mark}")
        dump_jsonl(mark)
    logger.debug(f"Dicoms offsets: {offset}")


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

    if not os.path.exists(path):
        logger.error(f"Session path does not exist: {path}")
        return 1

    path_dumps: str = os.path.join(path, "timing-dumps")
    if not os.path.exists(path_dumps):
        logger.error(f"Session timing-dumps path does not exist: {path_dumps}")
        return 1

    model: DumpModel = build_model(path_dumps)
    #logger.debug(f"Model: {model}")

    generate_marks(model)

    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)