from __future__ import annotations

import shutil
import sys
from pathlib import Path
from uuid import uuid4

import pytest


TEST_ROOT = Path(__file__).resolve().parent
AI_TEAM_ROOT = TEST_ROOT.parent
REPO_ROOT = AI_TEAM_ROOT.parent
WORKSPACE_TEMP_ROOT = REPO_ROOT / ".tmp-pytest-workspace"

for path in (REPO_ROOT, AI_TEAM_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


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
