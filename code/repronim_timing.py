from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Generator
import jsonlines
import pandas as pd
import logging

logger = logging.getLogger(__name__)


# common functions
def dump_jsonl(obj):
    print(obj.json())


def parse_jsonl_gen(path: str) -> Generator[dict, None, None]:
    with jsonlines.open(path) as reader:
        for obj in reader:
            yield obj


def parse_jsonl(path: str) -> List:
    return [obj for obj in parse_jsonl_gen(path)]


def parse_isotime(v: str) -> datetime:
    if not v:
        return None
    ts = pd.to_datetime(v)
    if ts.tzinfo is not None:
        ts = ts.tz_convert('America/New_York')
    isotime = ts.tz_localize(None)
    return isotime


def str_isotime(v: datetime) -> str:
    if not v:
        return None
    return v.strftime("%Y-%m-%dT%H:%M:%S.%f")


# define ReproNim clocks
class Clock(str, Enum):
    ISOTIME = "isotime"   # Reference NTP clock
    BIRCH = "birch"       # Birch clock
    DICOMS = "dicoms"     # DICOMs clock
    PSYCHOPY = "psychopy" # psychopy clock
    QRINFO = "qrinfo"     # QRInfo clock
    # ReproStim video clock, by now the same as QRInfo clock
    REPROSTIM_VIDEO = "reprostim_video"


# Define abstract timing map model
class TMapRecord(BaseModel):
    isotime: Optional[datetime] = Field(
        None, description="Reference time bound to NTP in isotime format")
    dicoms_isotime: Optional[datetime] = Field(
        None, description="Corresponding DICOMs clock time in isotime format")
    dicoms_offset: Optional[float] = Field(
        0.0, description="DICOMs offset in seconds from isotime")
    dicoms_deviation: Optional[float] = Field(
        0.0, description="Represents DICOMs time deviation ratio comparing "
                         "to master clock")
    birch_isotime: Optional[datetime] = Field(
        None, description="Corresponding birch clock time in isotime format")
    birch_offset: Optional[float] = Field(
        0.0, description="birch offset in seconds from isotime")
    birch_deviation: Optional[float] = Field(
        0.0, description="Represents birch time deviation ratio comparing "
                         "to master clock")
    reprostim_video_isotime: Optional[datetime] = Field(
        None, description="Corresponding ReproStim video clock time in "
                          "isotime format")
    reprostim_video_offset: Optional[float] = Field(
        0.0, description="ReproStim video offset in seconds from isotime")
    reprostim_video_deviation: Optional[float] = Field(
        0.0, description="Represents ReproStim video time deviation ratio "
                         "comparing to master clock")
    psychopy_isotime: Optional[datetime] = Field(
        None, description="Corresponding psychopy clock time in isotime format")
    psychopy_offset: Optional[float] = Field(
        0.0, description="psychopy offset in seconds from isotime")
    psychopy_deviation: Optional[float] = Field(
        0.0, description="Represents psychopy time deviation ratio "
                         "comparing to master clock")


# find tmap offset by clock
def get_tmap_offset(clock: Clock, tmap: TMapRecord) -> float:
    if clock == Clock.ISOTIME:
        return 0.0
    if clock == Clock.BIRCH:
        return tmap.birch_offset
    elif clock == Clock.DICOMS:
        return tmap.dicoms_offset
    elif clock == Clock.PSYCHOPY:
        return tmap.psychopy_offset
    elif clock == Clock.QRINFO:
        return tmap.reprostim_video_offset
    elif clock == Clock.REPROSTIM_VIDEO:
        return tmap.reprostim_video_offset
    else:
        raise ValueError(f"Unknown clock: {clock}")


# find tmap isotime by clock
def get_tmap_isotime(clock: Clock, tmap: TMapRecord) -> datetime:
    if clock == Clock.ISOTIME:
        return tmap.isotime
    if clock == Clock.BIRCH:
        return tmap.birch_isotime
    elif clock == Clock.DICOMS:
        return tmap.dicoms_isotime
    elif clock == Clock.PSYCHOPY:
        return tmap.psychopy_isotime
    elif clock == Clock.QRINFO:
        return tmap.reprostim_video_isotime
    elif clock == Clock.REPROSTIM_VIDEO:
        return tmap.reprostim_video_isotime
    else:
        raise ValueError(f"Unknown clock: {clock}")


# find tmap deviation by clock
def get_tmap_deviation(clock: Clock, tmap: TMapRecord) -> float:
    if clock == Clock.ISOTIME:
        return 1.0
    if clock == Clock.BIRCH:
        return tmap.birch_deviation
    elif clock == Clock.DICOMS:
        return tmap.dicoms_deviation
    elif clock == Clock.PSYCHOPY:
        return tmap.psychopy_deviation
    elif clock == Clock.QRINFO:
        return tmap.reprostim_video_deviation
    elif clock == Clock.REPROSTIM_VIDEO:
        return tmap.reprostim_video_deviation
    else:
        raise ValueError(f"Unknown clock: {clock}")


# Define ReproNim timing map service
class TMapService:
    def __init__(self, path_or_marks: str | List = None):
        self.marks = []
        if path_or_marks:
            self.load(path_or_marks)

    # convert datetime from one ReproNim clock to another
    def convert(self,
                from_clock: Clock,
                to_clock: Clock,
                dt_from: datetime) -> datetime:
        # bypass conversion if clocks are the same
        if from_clock == to_clock:
            return dt_from

        # skip empty datetime
        if not dt_from:
            return None

        tmap: TMapRecord = self.find_tmap(dt_from)
        # bypass conversion if tmap is not found
        if tmap is None:
            logger.warning(f"tmap not found for {dt_from}")
            return dt_from

        # calculate offset
        from_offset: float = get_tmap_offset(from_clock, tmap)
        to_offset: float = get_tmap_offset(to_clock, tmap)
        logger.debug(f"from_offset={from_offset}, to_offset={to_offset}")
        offset: float = to_offset - from_offset
        logger.debug(f"offset={offset}")

        return dt_from + pd.Timedelta(offset, unit='s')

    # find tmap record by datetime and clock in sorted
    # list of marks
    def find_tmap(self, dt: datetime) -> TMapRecord:
        if not self.marks or len(self.marks) == 0:
            return None
        if len(self.marks) == 1:
            return self.marks[0]

        last_mark = self.marks[0]

        for mark in self.marks:
            if mark.isotime > dt:
                break
            last_mark = mark
        return last_mark

    # load marks from file
    def load(self, path_or_marks: str | List):
        if isinstance(path_or_marks, str):
            for obj in parse_jsonl_gen(path_or_marks):
                self.marks.append(TMapRecord(**obj))
        else:
            for obj in path_or_marks:
                self.marks.append(TMapRecord(**obj))

        # sort by isotime
        self.marks.sort(key=lambda x: x.isotime)

    def to_label(self) -> str:
        # dump number of marks and each mark in format [N]=isotime
        if len(self.marks) == 0:
            return "TMap is empty"
        return f"TMap marks count {len(self.marks)} : " \
               + ", ".join([f"[{i}]={str_isotime(mark.isotime)}" for i, mark in enumerate(self.marks)])


