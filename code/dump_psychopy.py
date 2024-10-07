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


def dump_psychopy(session_id: str, logpath: str, range_start: datetime,
                  range_end: datetime, qrinfo_map: dict) -> None:
    with (jsonlines.open(logpath) as reader):
        for obj in reader:
            time_str = obj.get('time_formatted')
            if time_str:
                time_dt = pd.to_datetime(time_str).replace(tzinfo=None)
                evt: str = obj.get('event')
                keys: str = obj.get('keys')
                key0: str = keys[0] if keys and len(keys) > 0 else None
                logger.debug(f"Time: {time_dt}, event: {evt}, key0: {key0}")

                if range_start <= time_dt <= range_end and evt=='trigger' and key0=='5':
                    obj['id'] = None
                    obj['session_id'] = session_id
                    obj['isotime'] = time_dt.isoformat()
                    if obj.get('event') == 'trigger':
                        keys_time = pd.to_datetime(
                            obj.get('keys_time_str')
                        ).replace(tzinfo=None)
                        obj['isotime'] = keys_time.isoformat()
                    obj['qrinfo_id'] = None
                    key = get_qrinfo_map_key(obj)
                    if key in qrinfo_map:
                        obj['qrinfo_id'] = qrinfo_map[key].get('id')
                    # dump_jsonl(obj)
                    yield obj
                else:
                    logger.debug(f"Skip, out of study range: {obj}")


def find_psychopy_all_logfiles(psychopy_path: str) -> List[str]:
    lst = [os.path.basename(file) for file in os.listdir(psychopy_path) if file.endswith('.log')]
    return lst


def find_psychopy_logfiles(qrinfo_path: str) -> List[str]:
    logfn_ordered_dict = OrderedDict()

    with jsonlines.open(qrinfo_path) as reader:
        for obj in reader:
            if obj.get('type') == 'QrRecord':
                logfn = obj.get('data', {}).get('logfn')
                if logfn and logfn not in logfn_ordered_dict:
                    logfn_ordered_dict[logfn] = None

    return list(logfn_ordered_dict.keys())


def get_qrinfo_map_key(obj: dict) -> str:
    return f"{obj.get('logfn')}|{obj.get('keys_time_str')}"


# Build QRInfo map, where key if log file name + keys_time_str
def load_qrinfo_map(qrinfo_path: str) -> dict:
    m = {}
    with jsonlines.open(qrinfo_path) as reader:
        for obj in reader:
            if obj.get('type') == 'QrRecord':
                key = get_qrinfo_map_key(obj.get('data'))
                m[key] = obj
    return m


@click.command(help='Dump psychopy related logs only.')
@click.argument('path', type=click.Path(exists=True))
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level')
@click.pass_context
def main(ctx, path: str, log_level):
    logger.setLevel(log_level)
    logger.debug("dump_psychopy.py tool")
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

    psychopy_path: str = os.path.join(path, "psychopy")
    logger.info(f"Psychopy path : {psychopy_path}")

    if not os.path.exists(psychopy_path):
        logger.error(f"Psychopy path does not exist: {psychopy_path}")
        return 1

    qrinfo_path: str = os.path.join(dumps_path, "dump_qrinfo.jsonl")
    logger.info(f"QRInfo path   : {qrinfo_path}")

    if not os.path.exists(qrinfo_path):
        logger.error(f"QRInfo path does not exist: {qrinfo_path}")
        return 1

    # load tmap service
    _tmp_svc = get_tmap_svc()

    # load dumps config:
    cfg: DumpsConfig = do_config(path, _tmp_svc)

    # find the study range
    range_start, range_end = find_study_range(dump_dicoms_path)
    logger.info(f"Study range   : dicoms    {range_start} - {range_end}")
    range_start = get_tmap_svc().convert(Clock.DICOMS, Clock.PSYCHOPY,
                                         range_start)
    range_end = get_tmap_svc().convert(Clock.DICOMS, Clock.PSYCHOPY,
                                       range_end)
    logger.info(f"              : psychopy  {range_start} - {range_end}")


    # load QRInfo map
    logger.info(f"Loading QRInfo map from {qrinfo_path}")
    qrinfo_map = load_qrinfo_map(qrinfo_path)


    # find the psychopy log files
    #lst_logfiles = find_psychopy_logfiles(qrinfo_path) # filtered by QR codes
    lst_logfiles = find_psychopy_all_logfiles(psychopy_path) # use all log files
    logger.info(f"Psychopy log files: {lst_logfiles}")

    # dump the psychopy log files filtered by the study range
    lst: List[dict] = []
    for logfn in lst_logfiles:
        logpath = os.path.join(psychopy_path, logfn)
        logger.info(f"Psychopy log file: {logpath}")
        for obj in dump_psychopy(session_id, logpath,
                      range_start, range_end,
                      qrinfo_map):
            lst.append(obj)

    # sort list by isotime
    lst = sorted(lst, key=lambda x: x.get('isotime'))

    # generate IDs and dump
    for obj in lst:
        obj['id'] = generate_id('psychopy')
        dump_jsonl(obj)


    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)