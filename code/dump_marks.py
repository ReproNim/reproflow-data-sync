#!/usr/bin/env python3

import getpass
import os
import sys
from enum import Enum
from itertools import chain
from pathlib import Path

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import jsonlines
import pandas as pd

import click
import logging

from repronim_timing import (TMapService, Clock, parse_jsonl,
                             generate_id, dump_jsonl,
                             get_session_id, get_tmap_svc)
from repronim_dumps import (MarkRecord, init_config, get_config,
                            DumpsConfig, do_config)

# initialize the logger
# Note: all logs goes to stderr
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)
#logger.debug(f"name={__name__}")


# define ReproNim clocks
class Swimlane(str, Enum):
    DICOMS = "dicoms"
    BIRCH = "birch"
    PSYCHOPY = "psychopy"
    QRINFO = "qrinfo"
    REPROEVENTS = "reproevents"
    REPROSTIM_VIDEO = "reprostim_video"


# Define swimlane event/item data model
class EventData(BaseModel):
    id: Optional[str] = Field(None, description="Unique ID of the item")
    isotime: Optional[datetime] = Field(None, description="Event datetime timestamp")
    duration: Optional[float] = Field(None, description="Event duration in seconds "
                                                        "measured in swimlane clock")
    swimlane: Optional[object] = Field(None, description="Swimlane model reference")
    data: Optional[object] = Field({}, description="Data object")


# Define abstract series model
class SeriesData(BaseModel):
    data: Optional[List] = Field([], description="List of raw JSONL object "
                                                "in the series")
    events: Optional[List[EventData]] = Field([], description="List of event items "
                                                                "in the series")
    name: Optional[str] = Field(None, description="Series name")
    count: Optional[int] = Field(0, description="Number of object in series")
    swimlane: Optional[object] = Field(None, description="Swimlane model reference")
    isotime_start: Optional[datetime] = Field(None, description="Series start "
                                                                "datetime in local clock")
    isotime_end: Optional[datetime] = Field(None, description="Series end "
                                                                "datetime w/o "
                                                              "last item in local clock")
    interval: Optional[float] = Field(0.0, description="Series interval "
                                                       "in seconds")
    duration: Optional[float] = Field(0.0, description="Series duration w/o last "
                                                       "item at this moment")
    next_series_interval: Optional[float] = Field(0.0,
                                    description="Interval to next series if any in seconds, "
                                                "otherwise 0.0. Claculated as"
                                                "start-start interval between series")
    # contains approximate global datetime when series started
    synced_isotime_start: Optional[datetime] = Field(None, description="Series start global"
                                                                "datetime")
    # contains approximate global datetime when series ended
    synced_isotime_end: Optional[datetime] = Field(None, description="Series end global"
                                                                "datetime w/o "
                                                              "last item")



# Define swimlane object model
class SwimlaneModel(BaseModel):
    name: Optional[str] = Field(None, description="Swimlane name")
    clock: Optional[Clock] = Field(None, description="Clock model")
    event_type: Optional[str] = Field(None, description="Event type filter id any. "
                                                        "JSONL can contains more that one type")
    isotime_field: Optional[str] = Field(None, description="Field name for item in "
                                                           "swimlane containing "
                                                           "datetime in isotime format")
    duration_field: Optional[str] = Field(None, description="Optional precalculated "
                                                              "field with event "
                                                              "duration in seconds")
    data: Optional[List] = Field([], description="List of raw data object "
                                                 "from JSONL")
    events: Optional[List[EventData]] = Field([], description="List of event items "
                                                                "in the swimlane")
    series: Optional[List[SeriesData]] = Field([], description="List of detected series "
                                                               "for the swimlane")


# Define dump model
class DumpModel(BaseModel):
    session_id: Optional[str] = Field(None,
                                      description="Unique session identifier")
    birch: Optional[SwimlaneModel] = Field(SwimlaneModel(name=Swimlane.BIRCH,
                                                         clock=Clock.BIRCH,
                                                         isotime_field="isotime"),
                                           description="Birch swimlane")
    dicoms: Optional[SwimlaneModel] = Field(SwimlaneModel(name=Swimlane.DICOMS,
                                                          clock=Clock.DICOMS,
                                                          event_type="DicomsRecord",
                                                          isotime_field="acquisition_isotime"),
                                            description="DICOMs swimlane")
    psychopy: Optional[SwimlaneModel] = Field(SwimlaneModel(name=Swimlane.PSYCHOPY,
                                                            clock=Clock.PSYCHOPY,
                                                            isotime_field="isotime"),
                                              description="PsychoPy swimlane")
    qrinfo: Optional[SwimlaneModel] = Field(SwimlaneModel(name=Swimlane.QRINFO,
                                                          clock=Clock.QRINFO,
                                                          event_type="QrRecord",
                                                          isotime_field="isotime_start"),
                                            description="QRInfo swimlane")
    reproevents: Optional[SwimlaneModel] = Field(SwimlaneModel(name=Swimlane.REPROEVENTS,
                                                                clock=Clock.REPROEVENTS,
                                                                event_type="ReproeventsRecord",
                                                                isotime_field="isotime",
                                                                duration_field="duration"),
                                                    description="ReproEvents swimlane")
    map_by_id: Optional[dict] = Field({}, description="Map of all objects by "
                                                      "unique ID")

    @property
    def swimlanes(self) -> List[SwimlaneModel]:
        return [self.dicoms, self.birch, self.qrinfo,
                self.psychopy, self.reproevents]

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
        t1 = series[0].isotime
        t2 = series[-1].isotime
        return (t2-t1).total_seconds() / (len(series)-1)
    logger.debug(f"Series {series} has less than 2 dicoms")
    return 2.0


# Get swimlane dump file path
def get_dump_path(path: str, swimlane: SwimlaneModel) -> str:
    return os.path.join(path, f"dump_{swimlane.name}.jsonl")


# Find birch series based on DICOMs series interval
def find_swimlane_series(swimlane: SwimlaneModel,
                         interval: float) -> List[SeriesData]:
    lst: List[SeriesData] = []
    dt_min:float = interval * 0.8
    dt_max:float = interval * 1.2

    # check for an empty list
    if not swimlane.events:
        return lst

    # check for a list with less than 2 items
    if len(swimlane.events) < 2:
        return lst

    last_isotime: datetime = None
    evts: List = []
    for evt in chain(swimlane.events, [swimlane.events[0]]):
        isotime: datetime = evt.isotime
        if len(evts) == 0:
            evts.append(evt)
            last_isotime = isotime
            continue

        if dt_min <= evts[-1].duration <= dt_max:
            evts.append(evt)
        else:
            # consider only more than 5 objects in series
            if len(evts) > 5:
                sd: SeriesData = SeriesData()
                sd.swimlane = swimlane
                sd.events = evts
                sd.data = [o.data for o in evts]
                sd.count = len(evts)
                sd.name = f"{swimlane.name}-series-{(len(lst)+1)}"
                sd.isotime_start = evts[0].isotime
                sd.isotime_end = evts[-1].isotime
                sd.synced_isotime_start = get_tmap_svc().convert(
                    swimlane.clock, Clock.ISOTIME, sd.isotime_start)
                sd.synced_isotime_end = get_tmap_svc().convert(
                    swimlane.clock, Clock.ISOTIME, sd.isotime_end)
                sd.interval = (last_isotime - sd.isotime_start).total_seconds() / (sd.count-1)
                sd.next_series_interval = 0
                sd.duration = (sd.isotime_end - sd.isotime_start).total_seconds()
                if len(lst) > 0:
                    lst[-1].next_series_interval = (
                        (sd.isotime_start - lst[-1].isotime_start).total_seconds())
                lst.append(sd)
            else:
                logger.debug(f"Skip {swimlane.name} series (too small={len(evts)}): {[evt.id for evt in evts]}")
            evts = []
            evts.append(evt)

        last_isotime = isotime

    return lst


# Return list of list DICOMs object in each series
def find_dicoms_func_series(model: DumpModel) -> List[SeriesData]:
    df = pd.DataFrame(model.dicoms.data)
    # filter by type, study and series
    filtered_df = df[
        (df['type'] == 'DicomsRecord') &
        (df['study'] == 'dbic^QA') &
        (df['series'].str.startswith('func-'))
        ]

    # group by series folder, rather than only series name
    grouped_df = filtered_df.groupby('series_folder')

    lst: List = []
    last_sd: SeriesData = None
    for series, group in grouped_df:
        sd: SeriesData = SeriesData()
        sd.swimlane = model.dicoms
        sd.events = [model.get_by_id(uid) for uid in group['id']]
        sd.data = [model.get_by_id(uid).data for uid in group['id']]
        sd.count = len(sd.events)
        sd.name = series
        sd.isotime_start = sd.events[0].isotime
        sd.isotime_end = sd.events[-1].isotime
        sd.synced_isotime_start = get_tmap_svc().convert(
            Clock.DICOMS, Clock.ISOTIME, sd.isotime_start)
        sd.synced_isotime_end = get_tmap_svc().convert(
            Clock.DICOMS, Clock.ISOTIME, sd.isotime_end)
        sd.interval = calc_dicoms_series_interval(sd.events)
        sd.next_series_interval = 0.0
        sd.duration = (sd.isotime_end -
                       sd.isotime_start).total_seconds()
        if last_sd:
            last_sd.next_series_interval = (
                (sd.isotime_start - last_sd.isotime_start).total_seconds())
        lst.append(sd)
        last_sd = sd
    return lst


# match SeriesData object with another one and return score result if any
def match_series_data(cfg: DumpsConfig, sd1: SeriesData, sd2: SeriesData) -> (bool, float):
    # NOTE: the code contains hardcoded bypasses for qrinfo swimlane
    # because of the current problems with 0.3 sec in first QR code
    # so ideally it should be disabled in future once we fix the problem
    score: float = 0.0
    f_debug: bool = True
    #if sd1.name == '015-func-bold_task-rest_acq-med1_run-04' and sd2.name == 'birch-series-8':
    #    logger.debug(f"Matching: {sd1} with {sd2}")
    if f_debug:
        logger.debug(f"Matching: sd1={sd1.name} with sd2={sd2.name}")

    if not sd1 or not sd2:
        if f_debug:
            logger.debug(f" mismatch_0")
        return False, score

    # match item count
    if sd1.count != sd2.count:
        if f_debug:
            logger.debug(f" mismatch_7: {sd1.count} / {sd2.count}")
        return False, score

    k_min: float = 0.95
    k_max: float = 1.05

    # for QRINFO we allow 20% difference, because of the current problems with 0.3 sec
    if sd1.swimlane.name==Swimlane.QRINFO or sd2.swimlane.name==Swimlane.QRINFO:
        k_min = 0.80
        k_max = 1.20

    if f_debug:
        logger.debug(f" use k_min={k_min}, k_max={k_max}")

    # match interval corresponds to each other
    if sd1.interval and sd2.interval:
        t_min: float = sd1.interval * k_min
        t_max: float = sd1.interval * k_max
        if not (t_min <= sd2.interval <= t_max):
            if f_debug:
                logger.debug(f" mismatch_1: {sd1.interval} / {sd2.interval}")
            return False, score

    # match inter series interval matches as well
    if sd1.next_series_interval and sd2.next_series_interval:
        t_min: float = sd1.next_series_interval * k_min
        t_max: float = sd1.next_series_interval * k_max
        if not (t_min <= sd2.next_series_interval <= t_max):
            if f_debug:
                logger.debug(f" mismatch_2: {sd1.next_series_interval} / {sd2.next_series_interval}")
            return False, score

    # Kludge, skip check for QRINFO swimlane atm
    if sd2.swimlane.name!=Swimlane.QRINFO:
        if sd1.next_series_interval==0.0 and sd2.next_series_interval>0:
            if f_debug:
                logger.debug(f" mismatch_3: {sd1.next_series_interval} / {sd2.next_series_interval}")
            return False, score

        if sd1.next_series_interval>0 and sd2.next_series_interval==0.0:
            if f_debug:
                logger.debug(f" mismatch_4: {sd1.next_series_interval} / {sd2.next_series_interval}")
            return False, score

    #else:
    #    return False
        #if sd1.next_series_interval!=0.0 and sd2.next_series_interval!=0.0:
        #    return False

    # match synced start time
    synced_dt: float = abs((sd1.synced_isotime_start - sd2.synced_isotime_start).total_seconds())
    # for DICOMs series we allow 120 sec difference
    if sd1.swimlane.name==Swimlane.DICOMS or sd2.swimlane.name==Swimlane.DICOMS:
        # make interval strict in case DICOMS correction provided manually
        dicoms_dt = 2.0 if Swimlane.DICOMS in cfg.clock_offsets else 120.0
        # logger.debug(f"dicoms_dt={dicoms_dt}")
        if synced_dt > dicoms_dt :
            if f_debug:
                logger.debug(f" mismatch_5: {sd1.synced_isotime_start} / {sd2.synced_isotime_start}")
            return False, score
    else:
        if synced_dt > 2.0:
            if f_debug:
                logger.debug(f" mismatch_6: {sd1.synced_isotime_start} / {sd2.synced_isotime_start}")
            return False, score

    score += synced_dt

    logger.debug(f"Matched series data: {sd1.name} / {sd2.name}")
    logger.debug(f"    score                = {score}")
    logger.debug(f"    count                = {sd1.count} / {sd2.count}")
    logger.debug(f"    interval             = {sd1.interval} / {sd2.interval}")
    logger.debug(f"    next_series_interval = {sd1.next_series_interval} / {sd2.next_series_interval}")
    logger.debug(f"    isotime_start        = {sd1.isotime_start} / {sd2.isotime_start}")
    logger.debug(f"    isotime_end          = {sd1.isotime_end} / {sd2.isotime_end}")
    logger.debug(f"    synced_start         = {sd1.synced_isotime_start} / {sd2.synced_isotime_start}")
    logger.debug(f"    synced_end           = {sd1.synced_isotime_end} / {sd2.synced_isotime_end}")
    logger.debug(f"    series 1 IDs         = {sd1.events[0].id} .. {sd1.events[-1].id}")
    logger.debug(f"    series 2 IDs         = {sd2.events[0].id} .. {sd2.events[-1].id}")
    return True, score


def match_series(cfg: DumpsConfig, sd1: SeriesData,
                 series: List[SeriesData]) -> SeriesData:
    best_sd: SeriesData = None
    best_score: float = None
    for sd2 in series:
        match, score = match_series_data(cfg, sd1, sd2)
        if match:
            if best_sd:
               if score < best_score:
                   best_sd = sd2
                   best_score = score
            else:
                best_sd = sd2
                best_score = score
        else:
            # break cycle if found match previously
            if best_sd:
                break

    if best_sd:
        logger.debug(f"Matched series: {sd1.name} -> {best_sd.name}")
        logger.debug(f"         score: {best_score}")
    return best_sd


def build_swimlane_events(swimlane: SwimlaneModel):
    swimlane.events = []
    for obj in swimlane.data:
        if swimlane.event_type and obj.get('type') != swimlane.event_type:
            logger.debug(f"Skip event object, type is not {swimlane.event_type}: {obj.get('id')}")
            continue

        ed: EventData = EventData()
        ed.id = obj.get('id')
        ed.isotime = parse_isotime(obj.get(swimlane.isotime_field))
        if not ed.isotime:
            logger.error(f"!!! Invalid isotime for object: {obj}")

        # calculate duration if not provided
        if swimlane.duration_field:
            v = obj.get(swimlane.duration_field)
            # logger.debug(f"Duration of {ed.id}: {v}")
            ed.duration = float(v)
        else:
            if len(swimlane.events)>0:
                prev_ed = swimlane.events[-1]
                ed.duration = 0.0
                #logger.debug(f"prev_ed: {prev_ed.isotime}")
                #logger.debug(f"ed: {ed.isotime}")
                prev_ed.duration = (ed.isotime - prev_ed.isotime).total_seconds()
            else:
                ed.duration = 0.0

        ed.swimlane = swimlane
        ed.data = obj
        swimlane.events.append(ed)


def build_model(session_id: str, path: str) -> DumpModel:
    m: DumpModel = DumpModel()
    m.session_id = session_id

    # build swimlane data, events and map by id
    for sl in m.swimlanes:
        # first, load all JSONL data to memory
        sl.data = parse_jsonl(get_dump_path(path, sl))
        # build events data
        build_swimlane_events(sl)
        for evt in sl.events:
            #logger.debug(f"Object: {evt.data}")
            m.map_by_id[evt.id] = evt

    # as second, detect possible series in each swimlane
    m.dicoms.series = find_dicoms_func_series(m)

    interval: float = m.dicoms.series[0].interval
    if interval > 2.5 or interval < 1.5:
        logger.error(f"!!! Invalid DICOMs series interval: {interval}, use default 2.0")
        # logger.error(f"!!! Please check DICOMs series[0] data: {m.dicoms.series[0].data}")
        interval = 2.0

    for sl in chain([m.birch, m.qrinfo, m.psychopy, m.reproevents]):
        sl.series = find_swimlane_series(sl, interval)

    # dump short series info
    for sl in m.swimlanes:
        logger.debug(f"Swimlane: {sl.name}")
        logger.debug(f"  Found {len(sl.series)} {sl.name} series")
        for sd in sl.series:
            isotime_start: datetime = sd.synced_isotime_start
            isotime_end: datetime = sd.synced_isotime_end
            logger.debug(f"  Series: {sd.name}, "
                         f"count: {sd.count}, "
                         f"interval: {sd.interval:.3f}, "
                         f"next_series_interval: {sd.next_series_interval:.2f}, "
                         f"ids: {sd.events[0].id}..{sd.events[-1].id}, "
                         f"clock time: {sd.events[0].isotime.strftime('%H:%M:%S')}--{sd.events[-1].isotime.strftime('%H:%M:%S')}, "
                         f"isotime: {isotime_start.strftime('%H:%M:%S')}--{isotime_end.strftime('%H:%M:%S')}")

    # dump series info and data
    for sl in m.swimlanes:
        for sd in sl.series:
            logger.debug(f"{sl.name}.{sd.name} : {[evt.id for evt in sd.events]}")

    return m


def generate_marks(cfg: DumpsConfig, model: DumpModel):

    marks: List[MarkRecord] = []
    offset: dict = {}
    for dicoms_sd in model.dicoms.series:
        # generate start mark
        mark: MarkRecord = MarkRecord()
        mark.id = generate_id('mark')
        mark.session_id = model.session_id
        mark.kind = "Func series start"
        mark.name = f"{dicoms_sd.name}_start"
        mark.target_ids.append(dicoms_sd.events[0].id)
        mark.dicoms_isotime = dicoms_sd.isotime_start
        mark.dicoms_duration = dicoms_sd.duration

        # try to match series
        map_series: dict = {}
        for swiml in [model.birch, model.qrinfo, model.psychopy,
                      model.reproevents]:
            #logger.debug(f"match with swiml={swiml.name}")
            ref_sd: SeriesData = map_series.get(cfg.ref_swimlane) # Swimlane.BIRCH
            #logger.debug(f"ref_sd={cfg.ref_swimlane}")
            match_sd: SeriesData = match_series(cfg, ref_sd if ref_sd
                                                else dicoms_sd,
                                                swiml.series)
            if match_sd:
                map_series[swiml.name] = match_sd
                logger.debug(f"store map_series[{swiml.name}] -> {match_sd.name}")
                mark.target_ids.append(match_sd.events[0].id)
                setattr(mark, f"{swiml.name}_isotime", match_sd.isotime_start)
                setattr(mark, f"{swiml.name}_duration", match_sd.duration)
                offset[match_sd.name] = (dicoms_sd.isotime_start -
                                       match_sd.isotime_start).total_seconds()

        marks.append(mark)
        logger.debug(f"{mark.model_dump_json()}")
        # dump_jsonl(mark)

        # generate marks for each scan in series
        c = len(dicoms_sd.events)
        last_i = c - 1
        for i in range(c):
            mark = MarkRecord()
            mark.id = generate_id('mark')
            mark.session_id = model.session_id
            mark.kind = "Func series scan"
            mark.name = f"{dicoms_sd.name}_scan-{i}"
            mark.target_ids.append(dicoms_sd.events[i].id)
            mark.dicoms_isotime = dicoms_sd.events[i].isotime
            # skip duration for last item
            if i != last_i:
                mark.dicoms_duration = dicoms_sd.events[i].duration
            for k, v in map_series.items():
                mark.target_ids.append(v.events[i].id)
                setattr(mark, f"{k}_isotime", v.events[i].isotime)
                # skip duration for last item
                if i != last_i:
                    setattr(mark, f"{k}_duration", v.events[i].duration)
            marks.append(mark)
            logger.debug(f"{mark.model_dump_json()}")
            # dump_jsonl(mark)

        # generate end mark
        mark = MarkRecord()
        mark.id = generate_id('mark')
        mark.session_id = model.session_id
        mark.kind = "Func series end"
        mark.name = f"{dicoms_sd.name}_end"
        mark.target_ids.append(dicoms_sd.events[-1].id)
        mark.dicoms_isotime = dicoms_sd.isotime_end
        #mark.dicoms_duration = None
        logger.debug(f"Mark: {mark}")
        for k, v in map_series.items():
            mark.target_ids.append(v.events[-1].id)
            setattr(mark, f"{k}_isotime", v.isotime_end)
            #setattr(mark, f"{k}_duration", None)
        marks.append(mark)
        logger.debug(f"{mark.model_dump_json()}")
        # dump_jsonl(mark)

    logger.debug(f"Dicoms offsets: {offset}")
    logger.debug(f"Generated marks after pass 1, done:")
    for m in marks:
        logger.debug(f"  {m.id} : {m.target_ids}")

    # try to match marks with existing tmap also
    #
    # by now disable 2nd pass as it produces false results
    # in future it can be used only when tmap service is configured
    # with current session data
    #
    # logger.debug("Try to match marks with tmap service")
    for mark in []: # skip by now -->   for mark in marks:
        dicoms_isotime: datetime = mark.dicoms_isotime
        dicoms_cache: dict = {}
        dicoms_id: str = mark.target_ids[0]
        for swiml in [model.birch, model.qrinfo, model.psychopy,
                      model.reproevents]:
            for ser_sd in swiml.series:
                for evt in ser_sd.events:
                    obj_id: str = evt.id
                    isotime_1: datetime = evt.isotime

                    isotime_2: datetime = None
                    if swiml.clock in dicoms_cache:
                        isotime_2 = dicoms_cache[swiml.clock]
                    else:
                        isotime_2 = get_tmap_svc().convert(
                            model.dicoms.clock, swiml.clock,
                            dicoms_isotime)
                        dicoms_cache[swiml.clock] = isotime_2

                    dt: float = (isotime_1 - isotime_2).total_seconds()

                    threshold: float = 0.9
                     # logger.debug(f"{dicoms_id}/{obj_id}=, dt={dt}")
                    if (-threshold <= dt <= threshold and
                            obj_id not in mark.target_ids):
                        logger.debug(f"Time matched : {mark.name}")
                        logger.debug(f"             : {dt} sec, ({isotime_1} - {isotime_2})")
                        logger.debug(f"             : {dicoms_id} = {dicoms_isotime}")
                        logger.debug(f"             : {obj_id} = {isotime_2}")
                        mark.target_ids.append(obj_id)
                        if getattr(mark, f"{swiml.name}_isotime", None) is None:
                            logger.debug(f"             : set {swiml.name}_isotime= {isotime_1}")
                            setattr(mark, f"{swiml.name}_isotime", isotime_1)
                            if mark.kind == "Func series start":
                                logger.debug(f"             : set {swiml.name}_duration = {ser_sd.duration}")
                                setattr(mark, f"{swiml.name}_duration", ser_sd.duration)
                        # break next items
                        continue

    logger.debug("Done match marks with tmap service")
    logger.debug(f"Generated marks after pass 2, done:")
    for m in marks:
        logger.debug(f"  {m.id} : {m.target_ids}")


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

    # load dumps config:
    cfg: DumpsConfig = do_config(path, _tmp_svc)

    model: DumpModel = build_model(session_id, path_dumps)
    #logger.debug(f"Model: {model}")

    generate_marks(cfg, model)
    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)