#!/usr/bin/env python3
import getpass
import os
import sys

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
import pandas as pd
import jsonlines
import click
import logging


# initialize the logger
# Note: all logs goes to stderr
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)
#logger.debug(f"name={__name__}")


# Define abstract series model
class TMapRecord(BaseModel):
    isotime: Optional[datetime] = Field(
        None, description="Reference time bound to NTP in isotime format")
    dicoms_offset: Optional[float] = Field(
        0.0, description="DICOMs offset in seconds from isotime")
    dicoms_deviation: Optional[float] = Field(
        0.0, description="Represents DICOMs time deviation ratio comparing "
                         "to master clock")
    birch_offset: Optional[float] = Field(
        0.0, description="birch offset in seconds from isotime")
    birch_deviation: Optional[float] = Field(
        0.0, description="Represents birch time deviation ratio comparing "
                         "to master clock")
    qrinfo_offset: Optional[float] = Field(
        0.0, description="qrinfo offset in seconds from isotime")
    qrinfo_deviation: Optional[float] = Field(
        0.0, description="Represents qrinfo time deviation ratio "
                         "comparing to master clock")
    psychopy_offset: Optional[float] = Field(
        0.0, description="psychopy offset in seconds from isotime")
    psychopy_deviation: Optional[float] = Field(
        0.0, description="Represents psychopy time deviation ratio "
                         "comparing to master clock")



def dump_jsonl(obj):
    print(obj.json())


def parse_jsonl(path: str) -> List:
    # Load JSONL file
    lst = []
    with jsonlines.open(path) as reader:
        for obj in reader:
            lst.append(obj)
    return lst


def parse_isotime(v: str) -> datetime:
    if not v:
        return None
    ts = pd.to_datetime(v)
    if ts.tzinfo is not None:
        ts = ts.tz_convert('America/New_York')
    isotime = ts.tz_localize(None)
    return isotime


def find_full_mark(marks: List) -> Optional[dict]:
    for obj in marks:
        if (obj.get('type')=='MarkRecord' and
            obj.get('kind')=='Func series start' and
            obj.get('dicoms_isotime') is not None and
            obj.get('birch_isotime') is not None and
            obj.get('qrinfo_isotime') is not None and
            obj.get('psychopy_isotime') is not None):
            return obj
    return None


def calc_deviation(mark, field_name: str, ref_duration: float) -> float:
    duration: float = float(mark.get(field_name))
    if ref_duration !=0 :
        return duration / ref_duration


def calc_offset(mark, field_name: str, isotime: datetime) -> float:
    return (parse_isotime(mark.get(field_name)) - isotime).total_seconds()


def generate_tmap(path_marks: str):
    logger.debug(f"generate_tmap({path_marks})")

    marks: List = parse_jsonl(path_marks)
    fm = find_full_mark(marks)
    if fm is None:
        logger.error(f"Full/completed mark not found in {path_marks}")
        return 1
    logger.debug(f"Found full mark: {fm}")

    ref_isotime: datetime = parse_isotime(fm.get('birch_isotime'))
    ref_duration: float = float(fm.get('birch_duration'))

    tmr: TMapRecord = TMapRecord()
    tmr.isotime = ref_isotime
    # ATM we consider birch device time as the reference one
    tmr.birch_offset = 0.0
    tmr.birch_deviation = 1.0
    tmr.dicoms_offset = calc_offset(fm, 'dicoms_isotime', tmr.isotime)
    tmr.dicoms_deviation = calc_deviation(fm, 'dicoms_duration', ref_duration)
    tmr.qrinfo_offset = calc_offset(fm, 'qrinfo_isotime', tmr.isotime)
    tmr.qrinfo_deviation = calc_deviation(fm, 'qrinfo_duration', ref_duration)
    tmr.psychopy_offset = calc_offset(fm, 'psychopy_isotime', tmr.isotime)
    tmr.psychopy_deviation = calc_deviation(fm, 'psychopy_duration', ref_duration)

    dump_jsonl(tmr)
    return 0


@click.command(help='Build ReproNim timing map (tmap) table.')
@click.argument('path', type=click.Path(exists=True))
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level')
@click.pass_context
def main(ctx, path: str, log_level):
    logger.setLevel(log_level)
    logger.debug("dump_tmap.py tool")
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

    path_marks: str = os.path.join(path_dumps, "dump_marks.jsonl")
    if not os.path.exists(path_marks):
        logger.error(f"Dump marks path does not exist: {path_marks}")
        return 1

    return generate_tmap(path_marks)


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)