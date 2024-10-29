from datetime import datetime
from typing import Tuple, Optional, List, Set
from pydantic import BaseModel, Field
import yaml
import os
import logging

from repronim_timing import TMapService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# placeholder for common code to be used in the dump scripts
# data model, functions, etc.

######################################################################
# Dumps config model
class DumpsConfig(BaseModel):
    clock_offsets: Optional[dict] = Field(dict(), description="Optional clock "
                                                            "offsets from NTP time "
                                                            "to fix/force "
                                                            "manually certain "
                                                            "swimlanes. Key is clock "
                                                            "name and value is float "
                                                            "offset like in tmap.")
    ref_swimlane: Optional[str] = Field("birch", description="Reference swimlane used for "
                                                             "master clocks, default is birch.")
    skip_swimlanes: Optional[Set[str]] = Field(set(), description="List of swimlanes to "
                                                               "be skipped when calculating "
                                                               "tmap.")


######################################################################
# Data models

# Define model DICOM item
class DicomsRecord(BaseModel):
    type: Optional[str] = Field("DicomsRecord", description="JSON record type/class")
    id: Optional[str] = Field(None, description="DICOM object unique ID")
    session_id: Optional[str] = Field(None, description="Session unique ID")
    acquisition_time: Optional[str] = Field(None, description="MRI acquisition time")
    acquisition_date: Optional[str] = Field(None, description="MRI acquisition date")
    acquisition_isotime: Optional[datetime] = Field(None,
                                                    description="MRI acquisition "
                                                                "datetime in ISO "
                                                                "format")
    study: Optional[str] = Field(None, description="MRI study description")
    series: Optional[str] = Field(None, description="MRI series description")
    series_folder: Optional[str] = Field(None, description="Base name of the series folder")

# Define model for DICOM MRI study
class StudyRecord(BaseModel):
    type: Optional[str] = Field("StudyRecord", description="JSON record type/class")
    id: Optional[str] = Field(None, description="DICOM object unique ID")
    session_id: Optional[str] = Field(None, description="Session unique ID")
    name: Optional[str] = Field(None, description="MRI study description")
    series_count: Optional[int] = Field(0, description="Number of series in the study")
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



# Define model for DICOM MRI series
class SeriesRecord(BaseModel):
    type: Optional[str] = Field("SeriesRecord", description="JSON record type/class")
    id: Optional[str] = Field(None, description="DICOM object unique ID")
    session_id: Optional[str] = Field(None, description="Session unique ID")
    name: Optional[str] = Field(None, description="MRI series description")
    folder: Optional[str] = Field(None, description="Base name of the series folder")
    dicom_count: Optional[int] = Field(0, description="Number of DICOM data images"
                                                       " in the series")
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


# Pydantic model for reproevents record
class ReproeventsRecord(BaseModel):
    type: Optional[str] = Field("ReproeventsRecord", description="JSON record type/class")
    isotime: Optional[datetime] = Field(
        None, description="Reference time bound to NTP in isotime format, "
                          "reproevents clock")
    duration: Optional[float] = Field(0.0, description="Duration of the event "
                                                       "in seconds till the next event")
    state_duration: Optional[float] = Field(0.0, description="Duration of the state flag "
                                                             "set to 1")
    session_id: Optional[str] = Field(
        None, description="Unique session identifier generated by "
                          "collect_data.sh script, e.g. ses-20240528")
    id: Optional[str] = Field(None, description="Object unique ID")
    file_name: Optional[str] = Field(None, description="File name of the "
                                                       "reproevents CSV file for "
                                                       "reference purposes")
    state: Optional[int] = Field(None, description="State of the reproevent")
    # contains reproevent data like:
    #     callback_duration_us, state, client_time,
    #     client_time_iso, pin, callback_duration,
    #     server_time, action,
    #     roundtrip_delay, id
    server_time: Optional[float] = Field(None, description="Server time "
                                                              "in seconds")
    data: Optional[dict] = Field(None, description="Data record from original "
                                                   "reproevents CSV file "
                                                   "converted to JSON")


# Define synchronization mark/tag model
class MarkRecord(BaseModel):
    type: Optional[str] = Field("MarkRecord", description="JSON record type/class")
    session_id: Optional[str] = Field(None, description="Unique session identifier")
    id: Optional[str] = Field(None, description="Mark object unique ID")
    kind: Optional[str] = Field(None, description="Mark kind/type")
    name: Optional[str] = Field(None, description="Mark name")
    target_ids: Optional[List[str]] = Field([], description="List of unique "
                                                        "series in seconds")
    dicoms_isotime: Optional[datetime] = Field(None, description="DICOMs acquisition "
                                                            "time in ISO format")
    dicoms_duration: Optional[float] = Field(None, description="DICOMs series duration "
                                                               "in seconds")
    birch_isotime: Optional[datetime] = Field(None, description="Birch acquisition "
                                                           "time in ISO format")
    birch_duration: Optional[float] = Field(None, description="Birch series duration "
                                                              "in seconds")
    qrinfo_isotime: Optional[datetime] = Field(None, description="QRInfo acquisition "
                                                            "time in ISO format")
    qrinfo_duration: Optional[float] = Field(None, description="QRInfo series duration "
                                                               "in seconds")
    psychopy_isotime: Optional[datetime] = Field(None, description="PsychoPy acquisition "
                                                             "time in ISO format")
    psychopy_duration: Optional[float] = Field(None, description="Psychopy series duration "
                                                                "in seconds")
    reproevents_isotime: Optional[datetime] = Field(None, description="Reproevents acquisition "
                                                                     "time in ISO format")
    reproevents_duration: Optional[float] = Field(None, description="Reproevents series duration "
                                                                    "in seconds")

######################################################################
# Dumps config implementation
_dumps_config: Optional[DumpsConfig] = None

def get_config() -> DumpsConfig:
    """
    Returns the global DumpsConfig instance. If it's not initialized,
    raises an error.
    """
    global _dumps_config
    if _dumps_config is None:
        raise RuntimeError("DumpsConfig has not been initialized. "
                           "Call init_config() first.")
    return _dumps_config

def init_config(session_path: str) -> DumpsConfig:
    global _dumps_config
    if _dumps_config is None:
        config_path = os.path.join(session_path,
                                   'timing-dumps-config.yaml')
        if os.path.exists(config_path):
            logger.info(f"Loading dumps config from {config_path}")
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            _dumps_config = DumpsConfig(**config_data)
        else:
            logger.info(f"No dumps config found under {config_path} path, "
                         f"using defaults")
            _dumps_config = DumpsConfig()
    return _dumps_config

def do_config(session_path: str, tmap_svc: TMapService) -> DumpsConfig:
    # load dumps config:
    cfg: DumpsConfig = init_config(session_path)
    if cfg.clock_offsets:
        logger.debug(f"clock_offsets: {cfg.clock_offsets}")
        for clock, offset in cfg.clock_offsets.items():
            tmap_svc.force_offset(clock, offset)
    if cfg.skip_swimlanes:
        logger.debug(f"skip_swimlanes: {cfg.skip_swimlanes}")
    return cfg

