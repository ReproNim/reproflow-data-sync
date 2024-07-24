#!/usr/bin/env python3
import getpass
import os
import sys
from collections import OrderedDict

from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional

import click
import pydicom
import logging


# initialize the logger
# Note: all logs goes to stderr
logger = logging.getLogger(__name__)
logging.getLogger().addHandler(logging.StreamHandler(sys.stderr))
logger.setLevel(logging.DEBUG)
#logger.debug(f"name={__name__}")


# Define model DICOM item
class DicomRecord(BaseModel):
    type: Optional[str] = Field("DicomRecord", description="JSON record type/class")
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
    type: Optional[str] = Field("StudyRecord", description="JSON record type/class")
    name: Optional[str] = Field(None, description="MRI study description")
    time_start: Optional[str] = Field(None, description="MRI time study start")
    date_start: Optional[str] = Field(None, description="MRI date study start")
    isotime_start: Optional[datetime] = Field(None,
                                            description="MRI study start "
                                                        "datetime in ISO "
                                                        "format")
    range_isotime_start: Optional[datetime] = Field(None,
                                            description="Specify study range in "
                                                        "absolute ISO time format, "
                                                        "will be used by other "
                                                        "tools to for filtering.")
    time_end: Optional[str] = Field(None, description="MRI time study end")
    date_end: Optional[str] = Field(None, description="MRI date study end")
    isotime_end: Optional[datetime] = Field(None,
                                            description="MRI study end "
                                                        "datetime in ISO "
                                                        "format")
    range_isotime_end: Optional[datetime] = Field(None,
                                            description="Specify study range in "
                                                        "absolute ISO time format, "
                                                        "will be used by other "
                                                        "tools to for filtering.")
    duration: Optional[float] = Field(None, description="Duration of the "
                                                        "study in seconds")



# Define model for MRI series
class SeriesRecord(BaseModel):
    type: Optional[str] = Field("SeriesRecord", description="JSON record type/class")
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
    study: Optional[str] = Field(None, description="MRI study description")
    duration: Optional[float] = Field(None, description="Duration of the "
                                                        "series in seconds")


def calc_duration(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds()


def parse_mri_datetime(date: str, time: str) -> datetime:
    return datetime.strptime(f"{date} {time}", "%Y%m%d %H%M%S.%f")


def dump_dicoms_file(path: str):
    # DICOM tag for Content Time
    acq_time_tag = (0x0008, 0x0032)
    acq_date_tag = (0x0008, 0x0022)
    study_tag = (0x0008, 0x1030)
    series_tag = (0x0008, 0x103E)

    try:
        # Read the DICOM file
        ds = pydicom.dcmread(path)

        dr: DicomRecord = DicomRecord()
        # calc study
        if study_tag in ds:
            dr.study = ds[study_tag].value
            logger.info(f"    Study           = {dr.study}")
        else:
            logger.info(f"    Study not found")

        # calc series
        if series_tag in ds:
            dr.series = ds[series_tag].value
            logger.info(f"    Series          = {dr.series}")
        else:
            logger.info(f"    Series not found")

        # calc date
        if acq_date_tag in ds:
            dr.acquisition_date = ds[acq_date_tag].value
            logger.info(f"    AcquisitionDate = {dr.acquisition_date}")
        else:
            logger.info(f"    AcquisitionDate not found")

        # calc time
        if acq_time_tag in ds:
            dr.acquisition_time = ds[acq_time_tag].value
            logger.info(f"    AcquisitionTime = {dr.acquisition_time}")
        else:
            logger.info(f"    AcquisitionTime not found")

        if dr.acquisition_time and dr.acquisition_date:
            dr.acquisition_isotime = parse_mri_datetime(
                dr.acquisition_date, dr.acquisition_time)

        yield dr

    except Exception as e:
        logger.error(f"Error reading {path}: {e}")


def dump_dicoms_dir(path: str):
    #logger.debug(f"Reading DICOM dir {path}")
    for name in sorted(os.listdir(path)):
        # check if file is *.dcm
        if name.endswith('.dcm'):
            filepath = os.path.join(path, name)
            logger.debug(f"  {name}")
            yield from dump_dicoms_file(filepath)
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
            yield from dump_dicoms_dir(path2)
        else:
            logger.debug(f"Skipping file: {name}")


def dump_jsonl(obj):
    print(obj.json())


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
    logger.info(f"Started on    : {datetime.now()}, {getpass.getuser()}@{os.uname().nodename}")
    logger.debug(f"Working dir   : {os.getcwd()}")
    logger.info(f"Session path  : {path}")

    if not os.path.exists(path):
        logger.error(f"Session path does not exist: {path}")
        return 1

    # build path as path+DICOMS
    dicoms_path: str = os.path.join(path, "DICOMS")
    logger.info(f"DICOMS path   : {dicoms_path}")

    if not os.path.exists(dicoms_path):
        logger.error(f"DICOMS path does not exist: {dicoms_path}")
        return 1

    map_study = OrderedDict()
    map_series = OrderedDict()
    # specify delta time range as 1 hour
    range_delta = timedelta(minutes=60)
    for item in dump_dicoms_all(dicoms_path):
        if item.study:
            # build study map
            if item.study in map_study:
                sr: StudyRecord = map_study[item.study]
                # update time if any
                if item.acquisition_isotime < sr.isotime_start:
                    sr.isotime_start = item.acquisition_isotime
                    sr.range_isotime_start = sr.isotime_start - range_delta
                    sr.time_start = item.acquisition_time
                    sr.date_start = item.acquisition_date
                    sr.duration = calc_duration(sr.isotime_start,
                                                sr.isotime_end)
                if item.acquisition_isotime > sr.isotime_end:
                    sr.isotime_end = item.acquisition_isotime
                    sr.range_isotime_end = sr.isotime_end + range_delta
                    sr.time_end = item.acquisition_time
                    sr.date_end = item.acquisition_date
                    sr.duration = calc_duration(sr.isotime_start,
                                                sr.isotime_end)
            else:
                # create study
                sr: StudyRecord = StudyRecord(
                    name=item.study,
                    time_start=item.acquisition_time,
                    date_start=item.acquisition_date,
                    isotime_start=item.acquisition_isotime,
                    range_isotime_start=item.acquisition_isotime - range_delta,
                    time_end=item.acquisition_time,
                    date_end=item.acquisition_date,
                    isotime_end=item.acquisition_isotime,
                    range_isotime_end=item.acquisition_isotime + range_delta,
                    duration=0.0
                )
                map_study[item.study] = sr

            # build series map
            if item.series:
                skey: str = f"{item.study}|{item.series}"
                if skey in map_series:
                    ss: SeriesRecord = map_series[skey]
                    # update time if any
                    if item.acquisition_isotime < ss.isotime_start:
                        ss.isotime_start = item.acquisition_isotime
                        ss.time_start = item.acquisition_time
                        ss.date_start = item.acquisition_date
                        ss.duration = calc_duration(ss.isotime_start,
                                                    ss.isotime_end)
                    if item.acquisition_isotime > ss.isotime_end:
                        ss.isotime_end = item.acquisition_isotime
                        ss.time_end = item.acquisition_time
                        ss.date_end = item.acquisition_date
                        ss.duration = calc_duration(ss.isotime_start,
                                                    ss.isotime_end)
                else:
                    # create series
                    ss: SeriesRecord = SeriesRecord(
                        name=item.series,
                        time_start=item.acquisition_time,
                        date_start=item.acquisition_date,
                        isotime_start=item.acquisition_isotime,
                        time_end=item.acquisition_time,
                        date_end=item.acquisition_date,
                        isotime_end=item.acquisition_isotime,
                        study=item.study,
                        duration=0.0
                    )
                    map_series[skey] = ss

        dump_jsonl(item)

    #dump study
    for k, v in map_study.items():
        dump_jsonl(v)

    #dump series
    for k, v in map_series.items():
        dump_jsonl(v)

    return 0


if __name__ == "__main__":
    code = main(standalone_mode=False)
    logger.info(f"Exit on   : {datetime.now()}")
    logger.info(f"Exit code : {code}")
    sys.exit(code)