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


# initialize the logger
# Note: all logs goes to stderr
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)
#logger.debug(f"name={__name__}")


last_id: dict = { "psychopy": 0 }
def generate_id(name: str) -> str:
    # generate unique id based on int sequence
    global last_id
    last_id[name] += 1
    return f"{name}_{last_id[name]:06d}"


def dump_jsonl(obj):
    print(json.dumps(obj, ensure_ascii=False))


def dump_psychopy(logpath: str, range_start: datetime,
                  range_end: datetime):
    with (jsonlines.open(logpath) as reader):
        for obj in reader:
            time_str = obj.get('time_formatted')
            if time_str:
                time_dt = pd.to_datetime(time_str).replace(tzinfo=None)
                logger.debug(f"Time: {time_dt}")
                if range_start <= time_dt <= range_end:
                    obj['id'] = generate_id('psychopy')
                    obj['isotime'] = time_dt.isoformat()
                    if obj.get('event') == 'trigger':
                        keys_time = pd.to_datetime(
                            obj.get('keys_time_str')
                        ).replace(tzinfo=None)
                        obj['isotime'] = keys_time.isoformat()
                    dump_jsonl(obj)
                else:
                    logger.debug(f"Skip, out of study range: {obj}")


def find_psychopy_logfiles(qrinfo_path: str) -> List[str]:
    logfn_ordered_dict = OrderedDict()

    with jsonlines.open(qrinfo_path) as reader:
        for obj in reader:
            if obj.get('type') == 'QrRecord':
                logfn = obj.get('data', {}).get('logfn')
                if logfn and logfn not in logfn_ordered_dict:
                    logfn_ordered_dict[logfn] = None

    return list(logfn_ordered_dict.keys())


# Note: shared code
def find_study_range(dump_dicoms_path: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    with (jsonlines.open(dump_dicoms_path) as reader):
        for obj in reader:
            if obj.get('type') == 'StudyRecord' and obj.get('name') == 'dbic^QA':
                res = pd.to_datetime(obj['range_isotime_start']), pd.to_datetime(obj['range_isotime_end'])
                return res;
        return None, None


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

    # find the study range
    range_start, range_end = find_study_range(dump_dicoms_path)
    logger.info(f"Study range   : {range_start} - {range_end}")

    # find the psychopy log files
    lst_logfiles = find_psychopy_logfiles(qrinfo_path)
    logger.info(f"Psychopy log files: {lst_logfiles}")

    # dump the psychopy log files filtered by the study range
    for logfn in lst_logfiles:
        logpath = os.path.join(psychopy_path, logfn)
        logger.info(f"Psychopy log file: {logpath}")
        dump_psychopy(logpath, range_start, range_end)

    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)