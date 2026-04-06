from __future__ import annotations

from pathlib import Path

from state.factory import create_initial_state
from state.merge import merge_state
from state.store import StateStore


def test_merge_state_updates_nested_fields_without_losing_existing_values() -> None:
    original = create_initial_state(
        "Refactor runtime.",
        overrides={"review": {"approved": False, "feedback": "Needs changes.", "score": 0.4}},
    )
    updated = merge_state(original, {"review": {"approved": True}})

    assert updated["review"]["approved"] is True
    assert updated["review"]["feedback"] == "Needs changes."
    assert updated["review"]["score"] == 0.4


def test_state_store_round_trips_shared_state(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "state.json")
    state = create_initial_state(
        "Refactor runtime.",
        overrides={"coordination": {"repo_mode": "existing"}, "development": {"revision": 2}},
    )

    store.save(state)
    loaded = store.load()

    assert loaded["input"] == "Refactor runtime."
    assert loaded["coordination"]["repo_mode"] == "existing"
    assert loaded["development"]["revision"] == 2
