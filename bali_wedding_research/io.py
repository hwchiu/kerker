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


def _index_unique_records(
    records: list[dict[str, Any]],
    *,
    key: str,
    label: str,
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record[key]
        if record_id in indexed:
            raise ValueError(f"duplicate {label}: {record_id}")
        indexed[record_id] = record
    return indexed


def load_workspace_records(
    root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    ensure_workspace_layout(root)
    paths = workspace_paths(root)
    venues = load_validated_records(paths["venues"], validate_venue_record)
    sources = load_validated_records(paths["sources"], validate_source_record)
    photos = load_validated_records(paths["photos"], validate_photo_record)

    venues_by_id = _index_unique_records(venues, key="id", label="venue id")
    sources_by_id = _index_unique_records(sources, key="source_id", label="source_id")
    _index_unique_records(photos, key="photo_entry_id", label="photo_entry_id")
    source_ids_by_venue = {
        venue_id: set(venue["source_ids"])
        for venue_id, venue in venues_by_id.items()
    }

    for source in sources:
        if source["venue_id"] not in venues_by_id:
            raise ValueError(
                f"source {source['source_id']} references missing venue: {source['venue_id']}"
            )
        if source["source_id"] not in source_ids_by_venue[source["venue_id"]]:
            raise ValueError(
                f"source {source['source_id']} belongs to venue {source['venue_id']} "
                "but is missing from venue.source_ids"
            )

    for venue in venues:
        missing_sources = sorted(set(venue["source_ids"]) - set(sources_by_id))
        if missing_sources:
            raise ValueError(
                f"venue {venue['id']} references missing sources: {', '.join(missing_sources)}"
            )
        for source_id in venue["source_ids"]:
            source_venue_id = sources_by_id[source_id]["venue_id"]
            if source_venue_id != venue["id"]:
                raise ValueError(
                    f"venue {venue['id']} references source {source_id} "
                    f"owned by venue {source_venue_id}"
                )

    for photo in photos:
        if photo["source_id"] not in sources_by_id:
            raise ValueError(
                f"photo {photo['photo_entry_id']} references missing source: {photo['source_id']}"
            )
        if photo["venue_id"] not in venues_by_id:
            raise ValueError(
                f"photo {photo['photo_entry_id']} references missing venue: {photo['venue_id']}"
            )
        source_venue_id = sources_by_id[photo["source_id"]]["venue_id"]
        if source_venue_id != photo["venue_id"]:
            raise ValueError(
                "photo "
                f"{photo['photo_entry_id']} source {photo['source_id']} belongs to venue "
                f"{source_venue_id}, not {photo['venue_id']}"
            )

    return venues, sources, photos


def validate_workspace(root: Path) -> dict[str, int]:
    venues, sources, photos = load_workspace_records(root)
    return {
        "venues": len(venues),
        "sources": len(sources),
        "photos": len(photos),
    }
