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


# Define dump model
class DumpModel(BaseModel):
    birch: Optional[List] = Field([], description="List of Birch object "
                                                    "from JSONL")
    dicoms: Optional[List] = Field([], description="List of DICOMs "
                                                       "object from JSONL")
    psychopy: Optional[List] = Field([], description="List of PsychoPy "
                                                         "object from JSONL")
    qrinfo: Optional[List] = Field([], description="List of QRInfo "
                                                    "object from JSONL")
    map_by_id: Optional[dict] = Field({}, description="Map of all objects by "
                                                      "unique ID")

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
    birch_isotime: Optional[str] = Field(None, description="Birch acquisition "
                                                           "time in ISO format")
    qrinfo_isotime: Optional[str] = Field(None, description="QRInfo acquisition "
                                                            "time in ISO format")
    psychopy_isotime: Optional[str] = Field(None, description="PsychoPy acquisition "
                                                             "time in ISO format")

# Define abstract series model
class SeriesData(BaseModel):
    lst: Optional[List] = Field([], description="List JSONL object "
                                                "in series")
    name: Optional[str] = Field(None, description="Series name")
    count: Optional[int] = Field(0, description="Number of object in series")
    isotime_start: Optional[datetime] = Field(None, description="Series start "
                                                                "datetime")
    interval: Optional[float] = Field(0.0, description="Series interval "
                                                       "in seconds")
    next_series_interval: Optional[float] = Field(0.0,
                                    description="Interval to next series if any in seconds, "
                                                "otherwise 0.0. Claculated as"
                                                "start-start interval between series")


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


# return list of list DICOMs object in each series
def find_dicoms_func_series(model: DumpModel) -> List[SeriesData]:
    df = pd.DataFrame(model.dicoms)
    # filter by type, study and series
    filtered_df = df[
        (df['type'] == 'DicomRecord') &
        (df['study'] == 'dbic^QA') &
        (df['series'].str.startswith('func-'))
        ]

    # group by series
    grouped_df = filtered_df.groupby('series')

    #lst = [group['id'].tolist() for series, group in grouped_df]

    # find object from model data
    lst = [[model.get_by_id(uid) for uid in group['id']]
                       for series, group in grouped_df]
    lst: List = []
    last_sd: SeriesData = None
    for series, group in grouped_df:
        sd: SeriesData = SeriesData()
        sd.lst = [model.get_by_id(uid) for uid in group['id']]
        sd.count = len(sd.lst)
        sd.name = series
        sd.isotime_start = parse_isotime(
            sd.lst[0].get('acquisition_isotime'))
        sd.interval = calc_dicoms_series_interval(sd.lst)
        sd.next_series_interval = 0.0
        if last_sd:
            last_sd.next_series_interval = (
                (sd.isotime_start - last_sd.isotime_start).total_seconds())
        lst.append(sd)
        last_sd = sd
    return lst


def parse_jsonl(path: str) -> List:
    # Load JSONL file
    lst = []
    with jsonlines.open(path) as reader:
        for obj in reader:
            lst.append(obj)
    return lst


def build_model(path: str) -> DumpModel:
    m: DumpModel = DumpModel()
    m.dicoms = parse_jsonl(os.path.join(path, 'dump_dicoms.jsonl'))
    m.birch = parse_jsonl(os.path.join(path, 'dump_birch.jsonl'))
    m.psychopy = parse_jsonl(os.path.join(path, 'dump_psychopy.jsonl'))
    m.qrinfo = parse_jsonl(os.path.join(path, 'dump_qrinfo.jsonl'))
    for obj in chain(m.dicoms, m.birch, m.psychopy, m.qrinfo):
        #logger.debug(f"Object: {obj}")
        m.map_by_id[obj.get('id')] = obj
    return m


def generate_marks(model: DumpModel):
    dicoms_func: List[SeriesData] = find_dicoms_func_series(model)
    logger.debug(f"Found {len(dicoms_func)} func series")

    for sd in dicoms_func:
        logger.debug(f"Series: {sd}")
        mark: MarkRecord = MarkRecord()
        mark.id = generate_id('mark')
        mark.kind = "Func series start"
        mark.name = f"{sd.name}_start"
        mark.target_ids.append(sd.lst[0].get('id'))
        mark.dicoms_isotime = sd.isotime_start.isoformat()
        logger.debug(f"Mark: {mark}")
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