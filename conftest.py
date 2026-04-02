from __future__ import annotations

import shutil
import sys
from pathlib import Path
from uuid import uuid4

import pytest


REPO_ROOT = Path(__file__).resolve().parent
WORKSPACE_TEMP_ROOT = REPO_ROOT / ".tmp-pytest-workspace"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _make_temp_dir() -> Path:
    WORKSPACE_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    path = WORKSPACE_TEMP_ROOT / uuid4().hex
    path.mkdir(parents=True, exist_ok=False)
    return path


@pytest.fixture
def tmp_path() -> Path:
    path = _make_temp_dir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)

