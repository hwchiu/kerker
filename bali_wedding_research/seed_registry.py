from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

ALLOWED_SEED_STATUSES = {"candidate", "record_created", "rejected"}
STATUS_PRECEDENCE = {"candidate": 0, "rejected": 1, "record_created": 2}


def slugify_name(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not normalized:
        raise ValueError("seed names must contain at least one alphanumeric character")
    return normalized


def _validate_seed_entry(entry: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(entry, dict):
        raise ValueError("seed entry must be a dictionary")

    required_fields = {"seed_id", "name_en", "aliases", "region", "discovery_urls", "status"}
    missing = sorted(field for field in required_fields if field not in entry)
    if missing:
        raise ValueError(f"seed entry missing required fields: {', '.join(missing)}")

    candidate = deepcopy(entry)
    if not isinstance(candidate["seed_id"], str) or not candidate["seed_id"].strip():
        raise ValueError("seed_id must be a non-empty string")
    if not isinstance(candidate["name_en"], str) or not candidate["name_en"].strip():
        raise ValueError("name_en must be a non-empty string")
    if not isinstance(candidate["region"], str) or not candidate["region"].strip():
        raise ValueError("region must be a non-empty string")
    if candidate["status"] not in ALLOWED_SEED_STATUSES:
        raise ValueError("status must be candidate, record_created, or rejected")
    if not isinstance(candidate["aliases"], list):
        raise ValueError("aliases must be a list")
    if not isinstance(candidate["discovery_urls"], list) or not candidate["discovery_urls"]:
        raise ValueError("discovery_urls must be a non-empty list")

    candidate["aliases"] = sorted(
        {
            alias.strip()
            for alias in candidate["aliases"]
            if isinstance(alias, str) and alias.strip()
        }
    )
    candidate["discovery_urls"] = sorted(
        {
            url.strip()
            for url in candidate["discovery_urls"]
            if isinstance(url, str) and url.strip()
        }
    )
    if not candidate["discovery_urls"]:
        raise ValueError("discovery_urls must contain at least one URL")
    return candidate


def _alias_keys(entry: dict[str, Any]) -> set[str]:
    names = [entry["name_en"], *entry["aliases"]]
    return {slugify_name(name) for name in names}


def _group_aliases(entries: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            name
            for entry in entries
            for name in [entry["name_en"], *entry["aliases"]]
        }
    )


def _group_discovery_urls(entries: list[dict[str, Any]]) -> list[str]:
    return sorted(
        {
            url
            for entry in entries
            for url in entry["discovery_urls"]
        }
    )


def _group_keys(entries: list[dict[str, Any]]) -> set[str]:
    keys: set[str] = set()
    for entry in entries:
        keys.update(_alias_keys(entry))
    return keys


def _choose_primary_entry(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return min(
        entries,
        key=lambda entry: (-STATUS_PRECEDENCE[entry["status"]], entry["seed_id"]),
    )


def _build_canonical_entry(entries: list[dict[str, Any]]) -> dict[str, Any]:
    regions = {entry["region"] for entry in entries}
    if len(regions) != 1:
        raise ValueError("connected seed entries must share the same region")

    primary = _choose_primary_entry(entries)
    return {
        "seed_id": primary["seed_id"],
        "name_en": primary["name_en"],
        "aliases": _group_aliases(entries),
        "region": primary["region"],
        "discovery_urls": _group_discovery_urls(entries),
        "status": primary["status"],
    }


def merge_seed_registry(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged_groups: list[list[dict[str, Any]]] = []
    alias_to_group: dict[str, list[dict[str, Any]]] = {}

    for raw_entry in entries:
        entry = _validate_seed_entry(raw_entry)
        keys = _alias_keys(entry)
        matching_groups = [
            group
            for group in merged_groups
            if any(alias_to_group.get(key) is group for key in keys)
        ]

        if not matching_groups:
            group = [entry]
            merged_groups.append(group)
        else:
            group = matching_groups[0]
            group.append(entry)
            for duplicate in matching_groups[1:]:
                group.extend(duplicate)
                merged_groups.remove(duplicate)

        _build_canonical_entry(group)
        for key in _group_keys(group):
            alias_to_group[key] = group

    return [_build_canonical_entry(group) for group in merged_groups]
