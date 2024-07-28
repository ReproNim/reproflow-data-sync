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


last_id: dict = { "qr": 0 }
def generate_id(name: str) -> str:
    # generate unique id based on int sequence
    global last_id
    last_id[name] += 1
    return f"{name}_{last_id[name]:06d}"


def dump_jsonl(obj):
    print(json.dumps(obj, ensure_ascii=False))


def dump_qrinfo_file(path: str, range_start: datetime,
                    range_end: datetime):
    logger.debug(f"Processing QR : {path}")
    lst = []
    psum = None
    with (jsonlines.open(path) as reader):
        for obj in reader:
            if obj.get('type') == 'QrRecord':
                lst.append(obj)
            elif obj.get('type') == 'ParseSummary':
                psum = obj
            else:
                logger.debug(f"Skipping {obj}")

    if not psum:
        logger.error(f"Missing ParseSummary in {path}")
        return

    for obj in lst:
        isotime_start = pd.to_datetime(obj['isotime_start']
                                       ).replace(tzinfo=None)
        if range_start <= isotime_start <= range_end:
            # make flat, add videos info for info purposes
            obj['id'] = generate_id('qr')
            obj['video_file_name'] = psum.get('video_file_name')
            obj['video_isotime_start'] = psum.get('video_isotime_start')
            obj['video_isotime_end'] = psum.get('video_isotime_end')
            obj['video_frame_width'] = psum.get('video_frame_width')
            obj['video_frame_height'] = psum.get('video_frame_height')
            obj['video_frame_rate'] = psum.get('video_frame_rate')
            dump_jsonl(obj)
        else:
            logger.debug(f"Skip, out of study datetime range: {obj}")


def dump_qrinfo_all(path: str, range_start: datetime,
                    range_end: datetime):
    logger.debug(f"Reading parsed video QRs directory: {path}")
    for name in sorted(os.listdir(path)):
        # check if file is *.dcm
        if name.endswith('.qrinfo.jsonl'):
            filepath = os.path.join(path, name)
            logger.debug(f"  {name}")
            dump_qrinfo_file(filepath, range_start, range_end)
        else:
            logger.debug(f"  Skipping {name}")


@click.command(help='Dump qrinfo data tool.')
@click.argument('path', type=click.Path(exists=True))
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level')
@click.pass_context
def main(ctx, path: str, log_level):
    logger.setLevel(log_level)
    logger.debug("dump_qrinfo.py tool")
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

    parsed_videos_path: str = os.path.join(path, "timing-reprostim-videos")
    logger.info(f"Parsed QRs    : {parsed_videos_path}")

    if not os.path.exists(parsed_videos_path):
        logger.error(f"Parsed videos path does not exist: {parsed_videos_path}")
        return 1

    # find the study range
    range_start, range_end = find_study_range(dump_dicoms_path)
    logger.info(f"Study range   : {range_start} - {range_end}")

    dump_qrinfo_all(parsed_videos_path, range_start, range_end)

    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)