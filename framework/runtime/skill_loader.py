from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from spec_loader import repo_root


def _declared_skill_path(skill_path: str) -> Path:
    declared = Path(skill_path)
    if not declared.is_absolute():
        declared = repo_root() / declared
    return declared


def _skill_contract_path(skill_path: str) -> Path:
    declared = _declared_skill_path(skill_path)
    if declared.name == 'contract.yaml':
        return declared
    return declared / 'contract.yaml'


def _skill_name(skill_path: str) -> str:
    declared = Path(skill_path)
    if declared.name == 'contract.yaml':
        return declared.parent.name
    return declared.name


def load_skill_contract(skill_path: str) -> dict[str, Any]:
    path = _skill_contract_path(skill_path)
    try:
        with path.open('r', encoding='utf-8') as handle:
            data = yaml.safe_load(handle) or {}
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Missing skill contract for '{skill_path}' at '{path}'.") from exc
    if not isinstance(data, dict):
        raise ValueError(f'Expected mapping in {path}')
    data.setdefault('skill', _skill_name(skill_path))
    data.setdefault('skill_path', skill_path)
    return data


def load_role_skill_contracts(role_spec: dict[str, Any]) -> list[dict[str, Any]]:
    skills: list[str] = []
    primary = role_spec.get('primary_skill')
    if isinstance(primary, str):
        skills.append(primary)
    for item in role_spec.get('supporting_skills', []):
        if isinstance(item, str):
            skills.append(item)
    return [load_skill_contract(skill) for skill in skills]


def validate_skill_inputs(contracts: list[dict[str, Any]], available_inputs: set[str]) -> list[str]:
    messages: list[str] = []
    normalized_available = {item.strip().lower() for item in available_inputs}
    for contract in contracts:
        skill_name = str(contract.get('skill', 'unknown'))
        skill_path = str(contract.get('skill_path', skill_name))
        for required in contract.get('required_inputs', []):
            normalized = str(required).strip().lower()
            if normalized not in normalized_available:
                messages.append(
                    f"Skill '{skill_name}' from '{skill_path}' is missing required input '{required}'."
                )
    return messages


def validate_skill_outputs(contracts: list[dict[str, Any]]) -> list[str]:
    messages: list[str] = []
    owned_by_skill: dict[str, str] = {}
    for contract in contracts:
        skill_name = str(contract.get('skill', 'unknown'))
        for output in contract.get('owned_artifacts', []):
            existing = owned_by_skill.get(output)
            if existing and existing != skill_name:
                messages.append(f"Owned artifact conflict for '{output}' between {existing} and {skill_name}.")
            owned_by_skill[output] = skill_name
    return messages
