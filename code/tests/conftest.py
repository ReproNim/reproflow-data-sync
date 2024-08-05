import os
from pathlib import Path
import pytest
import logging
from code.repronim_timing import TMapService, TMapRecord

logger = logging.getLogger(__name__)

_tmap_svc: TMapService = None
_tmap_0: TMapRecord = None


@pytest.fixture(scope="session", autouse=True)
def init_tmap_service(path_tmap_jsonl: str):
    logger.info("Initialize TMapService")
    global _tmap_svc
    _tmap_svc = TMapService()
    _tmap_svc.load(path_tmap_jsonl)
    global _tmap_0
    if len(_tmap_svc.marks) > 0:
        _tmap_0 = _tmap_svc.marks[0]
    else:
        _tmap_0 = None
        logger.error("No timing marks loaded")


@pytest.fixture(scope="session")
def path_tmap_jsonl() -> str:
    return str(Path(__file__).with_name("data") / "tmap.jsonl")


@pytest.fixture
def tmap_svc() -> TMapService:
    global _tmap_svc
    return _tmap_svc

@pytest.fixture
def tmap_0(tmap_svc) -> TMapRecord:
    global _tmap_0
    return _tmap_0