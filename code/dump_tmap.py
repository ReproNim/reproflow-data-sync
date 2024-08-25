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

from repronim_timing import (TMapRecord, parse_jsonl, get_session_id,
                             parse_isotime, dump_jsonl, dump_csv)


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
            obj.get('reproevents_isotime') is not None and
            obj.get('psychopy_isotime') is not None):
            lst.append(obj)
    return lst


def find_partial_marks(marks: List) -> List[dict]:
    lst: List[dict] = []
    for obj in marks:
        if (obj.get('type')=='MarkRecord' and
            obj.get('birch_isotime') is not None and
            (obj.get('dicoms_isotime') is not None or
            obj.get('qrinfo_isotime') is not None or
            obj.get('reproevents_isotime') is not None or
            obj.get('psychopy_isotime') is not None)):
            lst.append(obj)
    return lst


def calc_deviation(mark, field_name: str, ref_duration: float) -> float:
    if not ref_duration:
        return None

    duration = mark.get(field_name)
    if duration is None:
        return None

    if ref_duration !=0 :
        return duration / ref_duration


def calc_offset(cur_isotime: datetime, ref_isotime: datetime) -> float:
    if cur_isotime is None or ref_isotime is None:
        return None
    return (cur_isotime - ref_isotime).total_seconds()


def get_dump_id(prefix: str, target_ids: List[str]) -> Optional[str]:
    if target_ids is None:
        return None
    # return comma string with comma separated IDs started with prefix
    return ",".join([id for id in target_ids if id.startswith(prefix)])


def generate_tmap(session_id: str, path_marks: str,
                  extended: bool, format: str) -> int:
    logger.debug(f"generate_tmap({path_marks})")

    marks: List = parse_jsonl(path_marks)
    # use partial or full marks depending on the mode
    fmarks = find_partial_marks(marks) if extended else find_full_marks(marks)
    if len(fmarks)<=0:
        logger.error(f"Full/completed mark not found in {path_marks}")
        return 1
    logger.debug(f"Found full mark count {len(fmarks)}: {fmarks}")

    tmap: List[TMapRecord] = []
    for fm in fmarks:
        ref_isotime: datetime = parse_isotime(fm.get('birch_isotime'))
        ref_duration = fm.get('birch_duration')
        if not ref_duration is None:
            ref_duration = float(ref_duration)

        tmr: TMapRecord = TMapRecord()
        tmr.isotime = ref_isotime
        tmr.duration = ref_duration
        tmr.session_id = session_id
        tmr.mark_id = fm.get('id')
        target_ids: List[str] = fm.get('target_ids')
        tmr.mark_name = fm.get('name')
        # ATM we consider birch device time as the reference one
        tmr.birch_id = get_dump_id("birch", target_ids)
        tmr.birch_isotime = ref_isotime
        tmr.birch_offset = 0.0
        tmr.birch_duration = fm.get('birch_duration')
        tmr.birch_deviation = 1.0
        tmr.dicoms_id = get_dump_id("dicoms", target_ids)
        tmr.dicoms_isotime = parse_isotime(fm.get('dicoms_isotime'))
        tmr.dicoms_offset = calc_offset(tmr.dicoms_isotime, tmr.isotime)
        tmr.dicoms_duration = fm.get('dicoms_duration')
        tmr.dicoms_deviation = calc_deviation(fm, 'dicoms_duration', ref_duration)
        tmr.qrinfo_id = get_dump_id("qrinfo", target_ids)
        tmr.reprostim_video_isotime = parse_isotime(fm.get('qrinfo_isotime'))
        tmr.reprostim_video_offset = calc_offset(tmr.reprostim_video_isotime, tmr.isotime)
        tmr.reprostim_video_duration = fm.get('qrinfo_duration')
        tmr.reprostim_video_deviation = calc_deviation(fm, 'qrinfo_duration', ref_duration)
        tmr.psychopy_id = get_dump_id("psychopy", target_ids)
        tmr.psychopy_isotime = parse_isotime(fm.get('psychopy_isotime'))
        tmr.psychopy_offset = calc_offset(tmr.psychopy_isotime, tmr.isotime)
        tmr.psychopy_duration = fm.get('psychopy_duration')
        tmr.psychopy_deviation = calc_deviation(fm, 'psychopy_duration', ref_duration)
        tmr.reproevents_id = get_dump_id("reproevents", target_ids)
        tmr.reproevents_isotime = parse_isotime(fm.get('reproevents_isotime'))
        tmr.reproevents_offset = calc_offset(tmr.reproevents_isotime, tmr.isotime)
        tmr.reproevents_duration = fm.get('reproevents_duration')
        tmr.reproevents_deviation = calc_deviation(fm, 'reproevents_duration', ref_duration)
        tmap.append(tmr)
        if format == 'jsonl':
            dump_jsonl(tmr)

    if format == 'csv':
        dump_csv(tmap)
    return 0


@click.command(help='Build ReproNim timing map (tmap) table.')
@click.argument('path', type=click.Path(exists=True))
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level')
@click.option('-f', '--format', default='JSONL',
              type=click.Choice(['JSONL', 'CSV']),
              help='Set the output format')
@click.option('-e', '--extended', is_flag=True,
              help='Enable extended mode for tmap, in this mode '
                   'will be generated partial tmap entries, when not '
                   'all clocks are available')
@click.pass_context
def main(ctx, path: str, log_level, extended, format):
    logger.setLevel(log_level)
    logger.debug("dump_tmap.py tool")
    logger.info(f"Started on    : {datetime.now()}, {getpass.getuser()}@{os.uname().nodename}")
    logger.debug(f"Working dir   : {os.getcwd()}")
    logger.info(f"Session path  : {path}")

    session_id: str = get_session_id(path)
    logger.info(f"Session ID    : {session_id}")


    format = format.lower()

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


    return generate_tmap(session_id, path_marks, extended, format)


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)