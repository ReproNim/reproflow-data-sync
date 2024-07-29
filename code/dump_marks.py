#!/usr/bin/env python3

import getpass
import os
import sys

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

import click
import logging


# initialize the logger
# Note: all logs goes to stderr
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)
#logger.debug(f"name={__name__}")


# Define synchronization mark/tag model
class MarkRecord(BaseModel):
    type: Optional[str] = Field("MarkRecord", description="JSON record type/class")
    id: Optional[str] = Field(None, description="Mark object unique ID")
    name: Optional[str] = Field(None, description="Mark name")
    target_ids: Optional[List[str]] = Field([], description="List of unique "
                                                        "series in seconds")


last_id: dict = { "mark": 0 }
def generate_id(name: str) -> str:
    # generate unique id based on int sequence
    global last_id
    last_id[name] += 1
    return f"{name}_{last_id[name]:06d}"


def dump_jsonl(obj):
    print(obj.json())


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

    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)