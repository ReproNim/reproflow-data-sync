#!/usr/bin/env python3
import getpass
import json
import os
import sys
from datetime import datetime
from typing import Tuple, Optional, List
from collections import OrderedDict

import click
import logging
import jsonlines
import pandas as pd

from repronim_dumps import DumpsConfig, do_config
from repronim_timing import (TMapService, Clock, dump_jsonl,
                             find_study_range, generate_id,
                             get_session_id, get_tmap_svc)


# initialize the logger
# Note: all logs goes to stderr
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)
#logger.debug(f"name={__name__}")


# Calculate the duration in seconds based on the tick time used
# by the birch system to recotd the 'time' field via pigpio.get_current_tick
# https://abyz.me.uk/rpi/pigpio/python.html#get_current_tick API.
# Note: this code works only with short time intervals, as the tick wraps around
# approximately every 71.6 minutes. For longer time intervals in future, we need to use
# the 'isotime' field to calculate the duration.
def calc_tick_interval(tick_start: float, tick_end: float) -> float:
    if not tick_start or not tick_end:
        return 0.0

    if tick_end >= tick_start:
        return tick_end - tick_start
    else:
        return (0xFFFFFFFF - tick_start + tick_end) + 1


def get_birch_isotime(obj: dict) -> datetime:
    iso_time_str: str = obj['iso_time']
    if not iso_time_str:
        return None
    iso_time_pd = pd.to_datetime(iso_time_str)
    iso_time_local = iso_time_pd.tz_convert('America/New_York')
    iso_time = iso_time_local.tz_localize(None)
    return iso_time


def safe_jsonl_reader(path):
    with open(path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    # Parse JSON and yield
                    yield json.loads(line)
                except json.JSONDecodeError:
                    # Optionally handle or log the invalid JSON lines
                    logger.error(f"Skipping invalid JSON line: {line}")
            else:
                logger.debug(f"Skipping empty or comment line: {line}")

def dump_birch_file(session_id: str, path: str, range_start: datetime,
                    range_end: datetime):
    logger.debug(f"Processing    : {path}")
    lst_obj: list = []
    lst_bit8: list = []
    for obj in safe_jsonl_reader(path):
        alink_byte = obj.get('alink_byte')
        alink_flags = obj.get('alink_flags')
        # check alink_byte bit 8 is on e.g. 496
        #if alink_byte and (alink_byte & 0x100) !=0 : # and obj.get('alink_flags') == 3:
        if alink_flags and (alink_flags & 0x0001) != 0:
            iso_time = get_birch_isotime(obj)
            logger.debug(f"  {iso_time.isoformat()} {obj['alink_byte']} {obj['alink_flags']}")
            if range_start <= iso_time <= range_end:
                obj['id'] = generate_id('birch')
                obj['session_id'] = session_id
                # represents duration on 8-th bit alink_flags
                obj['flag_duration_isotime'] = 0.0
                obj['flag_duration'] = 0.0
                # represents duration till next time 8-th bit will be on
                obj['duration_isotime'] = 0.0
                obj['duration'] = 0.0
                obj['isotime'] = iso_time.isoformat()
                #dump_jsonl(obj)

                # calculate the duration between the last 8-th bit on
                if len(lst_obj) > 0:
                    t2: datetime = get_birch_isotime(obj)
                    tick2: float = obj.get('time')
                    t1: datetime = get_birch_isotime(lst_obj[-1])
                    tick1: float = lst_obj[-1].get('time')
                    if t1 and t2:
                        obj['duration_isotime'] = (t2 - t1).total_seconds()
                    if tick1 and tick2:
                        obj['duration'] = calc_tick_interval(tick1, tick2)
                lst_obj.append(obj)
                lst_bit8.append(obj)
            else:
                logger.debug(f"Skipping out of study range "
                             f"isotime={iso_time.isoformat()},  {obj}")
        else:
            logger.debug(f"Skipping by alink_byte/alink_flags filter {obj}")
            #for o in lst_bit8:
            #    dump_jsonl(o)
            if len(lst_bit8)>0:
                # NOTE: maybe we need to calculate the duration
                # based on "time", which according to the birch
                # documentation cirresponds to the
                # https://abyz.me.uk/rpi/pigpio/python.html#get_current_tick
                # the number of microseconds since system boot. As an unsigned
                # 32 bit quantity tick wraps around approximately every 71.6 minutes.
                t2: datetime = get_birch_isotime(obj)
                tick2: float = obj.get('time')
                for o in lst_bit8:
                    t1: datetime = get_birch_isotime(o)
                    tick1: float = o.get('time')
                    if t1 and t2:
                        o['flag_duration_isotime'] = (t2 - t1).total_seconds()
                    if tick1 and tick2:
                        o['flag_duration'] = calc_tick_interval(tick1, tick2)

                lst_bit8 = []

    # dump the list of objects
    if lst_obj:
        for obj2 in lst_obj:
            dump_jsonl(obj2)


def dump_birch_all(session_id: str,  path: str, range_start: datetime,
                range_end: datetime):
    logger.debug(f"Reading birch directory: {path}")
    for name in sorted(os.listdir(path)):
        # check if file is *.dcm
        if name.endswith('.jsonl'):
            filepath = os.path.join(path, name)
            logger.debug(f"  {name}")
            dump_birch_file(session_id, filepath,
                            range_start, range_end)
        else:
            logger.debug(f"  Skipping {name}")


@click.command(help='Dump birch data tool.')
@click.argument('path', type=click.Path(exists=True))
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level')
@click.pass_context
def main(ctx, path: str, log_level):
    logger.setLevel(log_level)
    logger.debug("dump_birch.py tool")
    logger.info(f"Started on    : {datetime.now()}, {getpass.getuser()}@{os.uname().nodename}")
    logger.debug(f"Working dir   : {os.getcwd()}")
    logger.info(f"Session path  : {path}")

    session_id: str = get_session_id(path)
    logger.info(f"Session ID    : {session_id}")


    if not os.path.exists(path):
        logger.error(f"Session path does not exist: {path}")
        return 1

    # build path as path+timing-dumps
    dumps_path: str = os.path.join(path, "timing-dumps")
    logger.info(f"Dumps path    : {dumps_path}")

    if not os.path.exists(dumps_path):
        logger.error(f"Dumps path does not exist: {dumps_path}")
        return 1

    dump_dicoms_path = os.path.join(dumps_path, "dump_dicoms.jsonl")
    logger.info(f"DICOMS dump   : {dump_dicoms_path}")

    if not os.path.exists(dump_dicoms_path):
        logger.error(f"Dump DICOMS path does not exist: {dump_dicoms_path}")
        return 1

    birch_path: str = os.path.join(path, "birch")
    logger.info(f"Birch path    : {birch_path}")

    if not os.path.exists(birch_path):
        logger.error(f"Birch path does not exist: {birch_path}")
        return 1

    # load tmap service
    _tmp_svc = get_tmap_svc()

    # load dumps config:
    cfg: DumpsConfig = do_config(path, _tmp_svc)


    # find the study range
    range_start, range_end = find_study_range(dump_dicoms_path)
    logger.info(f"Study range   : dicoms {range_start} - {range_end}")
    range_start = get_tmap_svc().convert(Clock.DICOMS, Clock.BIRCH,
                                         range_start)
    range_end = get_tmap_svc().convert(Clock.DICOMS, Clock.BIRCH,
                                       range_end)
    logger.info(f"              : birch  {range_start} - {range_end}")


    dump_birch_all(session_id, birch_path, range_start, range_end)

    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)