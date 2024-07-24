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


# Note: shared code
def find_study_range(dump_dicoms_path: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    with (jsonlines.open(dump_dicoms_path) as reader):
        for obj in reader:
            if obj.get('type') == 'StudyRecord' and obj.get('name') == 'dbic^QA':
                res = pd.to_datetime(obj['range_isotime_start']), pd.to_datetime(obj['range_isotime_end'])
                return res;
        return None, None


def dump_jsonl(obj):
    print(json.dumps(obj, ensure_ascii=False))


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

def dump_birch_file(path: str, range_start: datetime,
                    range_end: datetime):
    logger.debug(f"Processing    : {path}")
    for obj in safe_jsonl_reader(path):
        if obj.get('alink_byte') == 496: # and obj.get('alink_flags') == 3:
            iso_time_str: str = obj['iso_time']
            iso_time_pd = pd.to_datetime(iso_time_str)
            iso_time_local = iso_time_pd.tz_convert('America/New_York')
            iso_time = iso_time_local.tz_localize(None)
            logger.debug(f"  {iso_time.isoformat()} {obj['alink_byte']} {obj['alink_flags']}")
            if range_start <= iso_time <= range_end:
                obj['isotime'] = iso_time.isoformat()
                dump_jsonl(obj)
            else:
                logger.debug(f"Skipping out of study range "
                             f"isotime={iso_time.isoformat()},  {obj}")
        else:
            logger.debug(f"Skipping by alink_byte/alink_flags filter {obj}")



def dump_birch_all(path: str, range_start: datetime,
                    range_end: datetime):
    logger.debug(f"Reading birch directory: {path}")
    for name in sorted(os.listdir(path)):
        # check if file is *.dcm
        if name.endswith('.jsonl'):
            filepath = os.path.join(path, name)
            logger.debug(f"  {name}")
            dump_birch_file(filepath, range_start, range_end)
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

    # find the study range
    range_start, range_end = find_study_range(dump_dicoms_path)
    logger.info(f"Study range   : {range_start} - {range_end}")

    dump_birch_all(birch_path, range_start, range_end)

    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)