#!/usr/bin/env python3

import os
import sys
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

import click
import pydicom
import logging


# initialize the logger
# Note: all logs goes to stderr
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)
logger.debug(f"name={__name__}")


# Define model DICOM item
class DicomRecord(BaseModel):
    type: Optional[str] = Field("dicom", description="JSON record type/class")
    acquisition_time: Optional[str] = Field(None, description="MRI acquisition time")
    acquisition_date: Optional[str] = Field(None, description="MRI acquisition date")
    acquisition_isotime: Optional[datetime] = Field(None,
                                                    description="MRI acquisition "
                                                                "datetime in ISO "
                                                                "format")
    study: Optional[str] = Field(None, description="MRI study description")
    series: Optional[str] = Field(None, description="MRI series description")

# Define model for MRI study
class StudyRecord(BaseModel):
    type: Optional[str] = Field("study", description="JSON record type/class")
    name: Optional[str] = Field(None, description="MRI study description")
    time_start: Optional[str] = Field(None, description="MRI time study start")
    date_start: Optional[str] = Field(None, description="MRI date study start")
    isotime_start: Optional[datetime] = Field(None,
                                            description="MRI study start "
                                                        "datetime in ISO "
                                                        "format")
    time_end: Optional[str] = Field(None, description="MRI time study end")
    date_end: Optional[str] = Field(None, description="MRI date study end")
    isotime_end: Optional[datetime] = Field(None,
                                            description="MRI study end "
                                                        "datetime in ISO "
                                                        "format")


# Define model for MRI series
class SeriesRecord(BaseModel):
    type: Optional[str] = Field("series", description="JSON record type/class")
    name: Optional[str] = Field(None, description="MRI series description")
    time_start: Optional[str] = Field(None, description="MRI time series start")
    date_start: Optional[str] = Field(None, description="MRI date series start")
    isotime_start: Optional[datetime] = Field(None,
                                            description="MRI series start "
                                                        "datetime in ISO "
                                                        "format")
    time_end: Optional[str] = Field(None, description="MRI time series end")
    date_end: Optional[str] = Field(None, description="MRI date series end")
    isotime_end: Optional[datetime] = Field(None,
                                            description="MRI series end "
                                                        "datetime in ISO "
                                                        "format")


def dump_dicoms_file(path: str):
    # DICOM tag for Content Time
    acq_time_tag = (0x0008, 0x0032)
    acq_date_tag = (0x0008, 0x0022)
    study_tag = (0x0008, 0x1030)
    series_tag = (0x0008, 0x103E)

    try:
        # Read the DICOM file
        ds = pydicom.dcmread(path)

        # calc study
        if study_tag in ds:
            logger.info(f"    Study           = {ds[study_tag].value}")
        else:
            logger.info(f"    Study not found")

        # calc series
        if series_tag in ds:
            logger.info(f"    Series          = {ds[series_tag].value}")
        else:
            logger.info(f"    Series not found")

        # calc date
        if acq_date_tag in ds:
            logger.info(f"    AcquisitionDate = {ds[acq_date_tag].value}")
        else:
            logger.info(f"    AcquisitionDate not found")

        # calc time
        if acq_time_tag in ds:
            logger.info(f"    AcquisitionTime = {ds[acq_time_tag].value}")
        else:
            logger.info(f"    AcquisitionTime not found")

    except Exception as e:
        logger.error(f"Error reading {path}: {e}")


def dump_dicoms_dir(path: str):
    #logger.debug(f"Reading DICOM dir {path}")
    for name in sorted(os.listdir(path)):
        # check if file is *.dcm
        if name.endswith('.dcm'):
            filepath = os.path.join(path, name)
            logger.debug(f"  {name}")
            dump_dicoms_file(filepath)
        else:
            logger.debug(f"Skipping file: {name}")


def dump_dicoms_all(path: str):
    logger.debug(f"Reading DICOM root : {path}")
    # Loop through all .dcm files in the directory
    for name in sorted(os.listdir(path)):
        # check if file is directory
        path2 = os.path.join(path, name)
        if os.path.isdir(path2):
            logger.debug(f"Reading DICOM dir  : {name}")
            dump_dicoms_dir(path2)
        else:
            logger.debug(f"Skipping file: {name}")


@click.command(help='Dump DICOM files date time info.')
@click.argument('path', type=click.Path(exists=True))
@click.option('--log-level', default='INFO',
              type=click.Choice(['DEBUG', 'INFO',
                                 'WARNING', 'ERROR',
                                 'CRITICAL']),
              help='Set the logging level')
@click.pass_context
def main(ctx, path: str, log_level):
    logger.setLevel(log_level)
    logger.debug("dump_dicoms.py tool")
    logger.debug(f"Working dir      : {os.getcwd()}")
    logger.info(f"Session path  : {path}")

    if not os.path.exists(path):
        logger.error(f"Session path does not exist: {path}")
        return 1

    # build path as path+DICOMS
    dicoms_path: str = os.path.join(path, "DICOMS")
    logger.info(f"DICOMS path   : {dicoms_path}")

    if not os.path.exists(path):
        logger.error(f"DICOMS path does not exist: {dicoms_path}")
        return 1

    dump_dicoms_all(dicoms_path)

    return 0


if __name__ == "__main__":
    code = main()
    sys.exit(code)