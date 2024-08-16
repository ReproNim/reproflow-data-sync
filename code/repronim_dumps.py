from datetime import datetime
from typing import Tuple, Optional, List
from pydantic import BaseModel, Field

# placeholder for common code to be used in the dump scripts
# data model, functions, etc.


######################################################################
# Data models

# Define model DICOM item
class DicomRecord(BaseModel):
    type: Optional[str] = Field("DicomRecord", description="JSON record type/class")
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
