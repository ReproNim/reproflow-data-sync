import logging
import os
from datetime import datetime

from code.repronim_timing import (TMapRecord, Clock,
                                  get_tmap_offset,
                                  get_tmap_deviation,
                                  TMapService,
                                  parse_isotime, str_isotime)
import pytest

logger = logging.getLogger(__name__)
logger.debug(f"name={__name__}")

def test_tmap_path(path_tmap_jsonl:str):
    logger.info(f"Testing TMapService with {path_tmap_jsonl}")
    # check file exists
    assert os.path.exists(path_tmap_jsonl)

def test_tmap_svc_created(tmap_svc):
    logger.info(f"Testing TMapService created")
    assert tmap_svc is not None
    assert len(tmap_svc.marks) > 0

def test_get_tmap_offset(tmap_0):
    logger.info(f"Testing get_tmap_offset")
    assert get_tmap_offset(Clock.ISOTIME, tmap_0) == 0.0
    assert get_tmap_offset(Clock.BIRCH, tmap_0) == 0.0
    assert get_tmap_offset(Clock.DICOMS, tmap_0) == 372.122385
    assert get_tmap_offset(Clock.PSYCHOPY, tmap_0) == -0.015225999999999962
    assert get_tmap_offset(Clock.QRINFO, tmap_0) == 0.317885
    assert get_tmap_offset(Clock.REPROSTIM_VIDEO, tmap_0) == 0.317885

def test_get_tmap_deviation(tmap_0):
    logger.info(f"Testing get_tmap_deviation")
    assert get_tmap_deviation(Clock.ISOTIME, tmap_0) == 1.0
    assert get_tmap_deviation(Clock.BIRCH, tmap_0) == 1.0
    assert get_tmap_deviation(Clock.DICOMS, tmap_0) == 1.0003138484699574
    assert get_tmap_deviation(Clock.PSYCHOPY, tmap_0) == 1.0002303937145993
    assert get_tmap_deviation(Clock.QRINFO, tmap_0) == 0.9872383174506716
    assert get_tmap_deviation(Clock.REPROSTIM_VIDEO, tmap_0) == 0.9872383174506716

@pytest.mark.parametrize("from_clock, from_dt, to_clock, to_dt", [
    (Clock.ISOTIME, "2024-06-04T13:54:19.385115", Clock.BIRCH, "2024-06-04T13:54:19.385115"),
    (Clock.ISOTIME, "2024-06-04T13:54:19.385115", Clock.DICOMS, "2024-06-04T14:00:31.507500"),
    (Clock.ISOTIME, "2024-06-04T13:54:19.385115", Clock.PSYCHOPY, "2024-06-04T13:54:19.369889"),
    (Clock.ISOTIME, "2024-06-04T13:54:19.385115", Clock.QRINFO, "2024-06-04T13:54:19.703000"),
    (Clock.ISOTIME, "2024-06-04T13:54:19.385115", Clock.REPROSTIM_VIDEO, "2024-06-04T13:54:19.703000"),
    # vice versa
    (Clock.BIRCH, "2024-06-04T13:54:19.385115", Clock.ISOTIME, "2024-06-04T13:54:19.385115"),
    (Clock.DICOMS, "2024-06-04T14:00:31.507500", Clock.ISOTIME, "2024-06-04T13:54:19.385115"),
    (Clock.PSYCHOPY, "2024-06-04T13:54:19.369889", Clock.ISOTIME, "2024-06-04T13:54:19.385115"),
    (Clock.QRINFO, "2024-06-04T13:54:19.703000", Clock.ISOTIME, "2024-06-04T13:54:19.385115"),
    (Clock.REPROSTIM_VIDEO, "2024-06-04T13:54:19.703000", Clock.ISOTIME, "2024-06-04T13:54:19.385115"),
    # between each other
    (Clock.BIRCH, "2024-06-04T13:54:19.385115", Clock.DICOMS, "2024-06-04T14:00:31.507500"),
    (Clock.BIRCH, "2024-06-04T13:54:19.385115", Clock.PSYCHOPY, "2024-06-04T13:54:19.369889"),
    (Clock.BIRCH, "2024-06-04T13:54:19.385115", Clock.QRINFO, "2024-06-04T13:54:19.703000"),
    (Clock.BIRCH, "2024-06-04T13:54:19.385115", Clock.REPROSTIM_VIDEO, "2024-06-04T13:54:19.703000"),
    (Clock.DICOMS, "2024-06-04T14:00:31.507500", Clock.BIRCH, "2024-06-04T13:54:19.385115"),
    (Clock.DICOMS, "2024-06-04T14:00:31.507500", Clock.PSYCHOPY, "2024-06-04T13:54:19.369889"),
    (Clock.DICOMS, "2024-06-04T14:00:31.507500", Clock.QRINFO, "2024-06-04T13:54:19.703000"),
    (Clock.DICOMS, "2024-06-04T14:00:31.507500", Clock.REPROSTIM_VIDEO, "2024-06-04T13:54:19.703000"),
    (Clock.PSYCHOPY, "2024-06-04T13:54:19.369889", Clock.BIRCH, "2024-06-04T13:54:19.385115"),
    (Clock.PSYCHOPY, "2024-06-04T13:54:19.369889", Clock.DICOMS, "2024-06-04T14:00:31.507500"),
    (Clock.PSYCHOPY, "2024-06-04T13:54:19.369889", Clock.QRINFO, "2024-06-04T13:54:19.703000"),
    (Clock.PSYCHOPY, "2024-06-04T13:54:19.369889", Clock.REPROSTIM_VIDEO, "2024-06-04T13:54:19.703000"),
    (Clock.QRINFO, "2024-06-04T13:54:19.703000", Clock.BIRCH, "2024-06-04T13:54:19.385115"),
    (Clock.QRINFO, "2024-06-04T13:54:19.703000", Clock.DICOMS, "2024-06-04T14:00:31.507500"),
    (Clock.QRINFO, "2024-06-04T13:54:19.703000", Clock.PSYCHOPY, "2024-06-04T13:54:19.369889"),
    (Clock.QRINFO, "2024-06-04T13:54:19.703000", Clock.REPROSTIM_VIDEO, "2024-06-04T13:54:19.703000"),
    (Clock.REPROSTIM_VIDEO, "2024-06-04T13:54:19.703000", Clock.BIRCH, "2024-06-04T13:54:19.385115"),
    (Clock.REPROSTIM_VIDEO, "2024-06-04T13:54:19.703000", Clock.DICOMS, "2024-06-04T14:00:31.507500"),
    (Clock.REPROSTIM_VIDEO, "2024-06-04T13:54:19.703000", Clock.PSYCHOPY, "2024-06-04T13:54:19.369889"),
    (Clock.REPROSTIM_VIDEO, "2024-06-04T13:54:19.703000", Clock.QRINFO, "2024-06-04T13:54:19.703000"),
])
def test_tmap_svc_convert(tmap_svc: TMapService,
                          from_clock: Clock, from_dt: str,
                          to_clock: Clock, to_dt: str):
    logger.info(f"Testing TMapService.convert")
    logger.info(f"from_clock={from_clock}, from_dt={from_dt}, to_clock={to_clock}, to_dt={to_dt}")
    from_isotime: datetime = parse_isotime(from_dt)
    to_isotime: datetime = tmap_svc.convert(from_clock, to_clock, from_isotime)
    to_isotime_str: str = str_isotime(to_isotime)
    logger.info(f"to_isotime={to_isotime_str}")
    assert to_isotime_str == to_dt


