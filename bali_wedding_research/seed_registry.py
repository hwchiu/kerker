from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

ALLOWED_SEED_STATUSES = {"candidate", "record_created", "rejected"}


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


def merge_seed_registry(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    alias_to_entry: dict[str, dict[str, Any]] = {}

    for raw_entry in entries:
        entry = _validate_seed_entry(raw_entry)
        keys = _alias_keys(entry)
        existing = next((alias_to_entry[key] for key in keys if key in alias_to_entry), None)

        if existing is None:
            canonical = {
                "seed_id": entry["seed_id"],
                "name_en": entry["name_en"],
                "aliases": sorted({entry["name_en"], *entry["aliases"]}),
                "region": entry["region"],
                "discovery_urls": entry["discovery_urls"],
                "status": entry["status"],
            }
            merged.append(canonical)
            for key in keys:
                alias_to_entry[key] = canonical
            continue

        existing["aliases"] = sorted(
            set(existing["aliases"]) | {entry["name_en"]} | set(entry["aliases"])
        )
        existing["discovery_urls"] = sorted(
            set(existing["discovery_urls"]) | set(entry["discovery_urls"])
        )
        for key in keys:
            alias_to_entry[key] = existing

    return merged
