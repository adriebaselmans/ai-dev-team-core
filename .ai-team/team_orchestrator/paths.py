"""Canonical path helpers for the team_orchestrator package.

Modules in this package previously each defined their own ``repo_root``
helper using ``Path(__file__).resolve().parents[2]``. They now share this
single source of truth.
"""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the repository root that contains the ``.ai-team/`` directory."""
    return Path(__file__).resolve().parents[2]


def ai_team_root() -> Path:
    return repo_root() / ".ai-team"
