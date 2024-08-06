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
from repronim_timing import (TMapRecord, parse_jsonl,
                             parse_isotime, dump_jsonl)


# initialize the logger
# Note: all logs goes to stderr
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)
#logger.debug(f"name={__name__}")



def find_full_marks(marks: List) -> List[dict]:
    lst: List[dict] = []
    for obj in marks:
        if (obj.get('type')=='MarkRecord' and
            obj.get('kind')=='Func series start' and
            obj.get('dicoms_isotime') is not None and
            obj.get('birch_isotime') is not None and
            obj.get('qrinfo_isotime') is not None and
            obj.get('psychopy_isotime') is not None):
            lst.append(obj)
    return lst


def calc_deviation(mark, field_name: str, ref_duration: float) -> float:
    duration: float = float(mark.get(field_name))
    if ref_duration !=0 :
        return duration / ref_duration


def calc_offset(cur_isotime: datetime, ref_isotime: datetime) -> float:
    return (cur_isotime - ref_isotime).total_seconds()


def generate_tmap(path_marks: str):
    logger.debug(f"generate_tmap({path_marks})")

    marks: List = parse_jsonl(path_marks)
    fmarks = find_full_marks(marks)
    if len(fmarks)<=0:
        logger.error(f"Full/completed mark not found in {path_marks}")
        return 1
    logger.debug(f"Found full mark count {len(fmarks)}: {fmarks}")

    for fm in fmarks:
        ref_isotime: datetime = parse_isotime(fm.get('birch_isotime'))
        ref_duration: float = float(fm.get('birch_duration'))

        tmr: TMapRecord = TMapRecord()
        tmr.isotime = ref_isotime
        # ATM we consider birch device time as the reference one
        tmr.birch_isotime = ref_isotime
        tmr.birch_offset = 0.0
        tmr.birch_deviation = 1.0
        tmr.dicoms_isotime = parse_isotime(fm.get('dicoms_isotime'))
        tmr.dicoms_offset = calc_offset(tmr.dicoms_isotime, tmr.isotime)
        tmr.dicoms_deviation = calc_deviation(fm, 'dicoms_duration', ref_duration)
        tmr.reprostim_video_isotime = parse_isotime(fm.get('qrinfo_isotime'))
        tmr.reprostim_video_offset = calc_offset(tmr.reprostim_video_isotime, tmr.isotime)
        tmr.reprostim_video_deviation = calc_deviation(fm, 'qrinfo_duration', ref_duration)
        tmr.psychopy_isotime = parse_isotime(fm.get('psychopy_isotime'))
        tmr.psychopy_offset = calc_offset(tmr.psychopy_isotime, tmr.isotime)
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