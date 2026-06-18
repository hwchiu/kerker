from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .paths import ensure_workspace_layout, workspace_paths
from .schema import validate_photo_record, validate_source_record, validate_venue_record


def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_validated_records(
    directory: Path,
    validator: Callable[[dict[str, Any]], dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        payload = load_json_file(path)
        if isinstance(payload, list):
            for item in payload:
                records.append(validator(item))
        else:
            records.append(validator(payload))
    return records


def load_workspace_records(
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ensure_workspace_layout(root)
    paths = workspace_paths(root)
    venues = load_validated_records(paths["venues"], validate_venue_record)
    sources = load_validated_records(paths["sources"], validate_source_record)
    photos = load_validated_records(paths["photos"], validate_photo_record)

    source_ids = {source["source_id"] for source in sources}
    venue_ids = {venue["id"] for venue in venues}

    for venue in venues:
        missing_sources = sorted(set(venue["source_ids"]) - source_ids)
        if missing_sources:
            raise ValueError(
                f"venue {venue['id']} references missing sources: {', '.join(missing_sources)}"
            )

    for photo in photos:
        if photo["source_id"] not in source_ids:
            raise ValueError(f"photo {photo['photo_entry_id']} references missing source")
        if photo["venue_id"] not in venue_ids:
            raise ValueError(f"photo {photo['photo_entry_id']} references missing venue")

    return venues, sources, photos


def validate_workspace(root: Path) -> dict[str, int]:
    venues, sources, photos = load_workspace_records(root)
    return {
        "venues": len(venues),
        "sources": len(sources),
        "photos": len(photos),
    }
