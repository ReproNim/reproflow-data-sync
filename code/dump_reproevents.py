#!/usr/bin/env python3
import getpass
import json
import os
import sys
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Tuple, Optional, List
from collections import OrderedDict

import click
import logging
import jsonlines
import pandas as pd

from repronim_timing import (TMapService, Clock, dump_jsonl,
                             find_study_range, generate_id,
                             get_session_id, get_tmap_svc, parse_isotime)

from repronim_dumps import ReproeventsRecord


# initialize the logger
# Note: all logs goes to stderr
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)
#logger.debug(f"name={__name__}")



def get_reproevents_isotime(obj: dict) -> datetime:
    iso_time_str: str = obj['client_time_iso']
    return parse_isotime(iso_time_str)


# Function to convert a reproevents CSV row to ReproeventsRecord
def row_to_model(row, session_id:str, file_name: str):
    data_dict = row.to_dict()
    return ReproeventsRecord(
        isotime=get_reproevents_isotime(row),
        duration=0.0,
        state_duration=0.0,
        session_id=session_id,
        id=None,
        file_name=file_name,
        state=int(data_dict['state']),
        server_time=float(data_dict['server_time']),
        data=data_dict  # Put all as 'data' dictionary
    )

def dump_revents_file(session_id: str, path: str, range_start: datetime,
                    range_end: datetime):
    logger.debug(f"Processing reproevents : {path}")
    # Read CSV file into a pandas DataFrame
    df = pd.read_csv(path)
    file_name: str = os.path.basename(path)
    lst: List[ReproeventsRecord] = []

    for _, row in df.iterrows():
        obj = row_to_model(row, session_id, file_name)
        if range_start <= obj.isotime <= range_end:
            if obj.state == 1:
                # calc duration for prev item
                if len(lst) > 0:
                    prev_obj = lst[-1]
                    prev_obj.duration = obj.server_time - prev_obj.server_time

                obj.id = generate_id("reproevents")
                lst.append(obj)
                #dump_jsonl(obj)
            else:
                logger.debug(f"Skip reproevents, state is not 1: {obj}")
                # calc state_duration for prev item
                if len(lst) > 0:
                    prev_obj = lst[-1]
                    prev_obj.state_duration = obj.server_time - prev_obj.server_time
        else:
            logger.debug(f"Skip reproevents, out of study datetime range: {obj}")

    # dump all records to as jsonl
    for obj in lst:
        dump_jsonl(obj)

def dump_revents_all(session_id: str, path: str, range_start: datetime,
                    range_end: datetime):
    logger.debug(f"Reading reproevent dir : {path}")
    for name in sorted(os.listdir(path)):
        # check if file is *.dcm
        if name.endswith('.csv'):
            filepath = os.path.join(path, name)
            logger.debug(f"  {name}")
            dump_revents_file(session_id, filepath,
                             range_start, range_end)
        else:
            logger.debug(f"  Skipping {name}")


@click.command(help='Dump reproevents data tool.')
@click.argument('path', type=click.Path(exists=True))
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level')
@click.pass_context
def main(ctx, path: str, log_level):
    logger.setLevel(log_level)
    logger.debug("dump_reproevents.py tool")
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

    revents_path: str = os.path.join(path, "reproevents")
    logger.info(f"Reproevents path: {revents_path}")

    if not os.path.exists(revents_path):
        logger.error(f"Reproevents path does not exist: {revents_path}")
        return 1

    # load tmap service
    _tmp_svc = get_tmap_svc()

    # find the study range
    range_start, range_end = find_study_range(dump_dicoms_path)
    logger.info(f"Study range   : dicoms      {range_start} - {range_end}")
    range_start = get_tmap_svc().convert(Clock.DICOMS, Clock.REPROEVENTS,
                                         range_start)
    range_end = get_tmap_svc().convert(Clock.DICOMS, Clock.REPROEVENTS,
                                       range_end)
    logger.info(f"              : reproevents {range_start} - {range_end}")

    dump_revents_all(session_id, revents_path,
                     range_start, range_end)
    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)