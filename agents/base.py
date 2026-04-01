from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any


class AgentContractError(ValueError):
    """Raised when an agent returns fields outside its contract."""


class Agent(ABC):
    """Stateless role agent that reads shared state and returns partial updates."""

    def __init__(self, role_key: str, owned_fields: set[str] | frozenset[str]) -> None:
        self.role_key = role_key
        self.owned_fields = frozenset(owned_fields)

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        snapshot = deepcopy(state)
        update = self._run(snapshot)
        if not isinstance(update, dict):
            raise AgentContractError(
                f"Agent '{self.role_key}' must return a mapping, got {type(update).__name__}."
            )
        unexpected = sorted(set(update) - self.owned_fields)
        if unexpected:
            raise AgentContractError(
                f"Agent '{self.role_key}' attempted to write unowned fields: {', '.join(unexpected)}."
            )
        return deepcopy(update)

    @abstractmethod
    def _run(self, state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
