from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .io import load_workspace_records, write_json_file
from .paths import workspace_paths
from .schema import summarize_photo_coverage


def build_derived_venue_entry(
    venue: dict[str, Any],
    photos: list[dict[str, Any]],
) -> dict[str, Any]:
    coverage = summarize_photo_coverage(photos)
    return {
        "id": venue["id"],
        "name_zh": venue["name_zh"],
        "name_en_official": venue["name_en_official"],
        "region": venue["region"],
        "venue_types": venue["venue_types"],
        "recommended_guest_size_band": venue["recommended_guest_size_band"],
        "pricing_status": venue["pricing_status"],
        "price_band_normalized": venue["price_band_normalized"],
        "price_summary_text": venue["price_summary_text"],
        "rain_backup_status": venue["rain_backup_status"],
        "accommodation_fit": venue["accommodation_fit"],
        "restriction_level": venue["restriction_level"],
        "traffic_risk_level": venue["traffic_risk_level"],
        "best_for": venue["best_for"],
        "not_ideal_for": venue["not_ideal_for"],
        "key_strengths": venue["key_strengths"],
        "key_risks": venue["key_risks"],
        "open_questions": venue["open_questions"],
        "source_count": len(venue["source_ids"]),
        "photo_count": len(photos),
        **coverage,
    }


def build_derived_indexes(root: Path) -> dict[str, list[dict[str, Any]]]:
    venues, _, photos = load_workspace_records(root)
    photos_by_venue: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for photo in photos:
        photos_by_venue[photo["venue_id"]].append(photo)

    derived_venues = [
        build_derived_venue_entry(venue, photos_by_venue.get(venue["id"], []))
        for venue in venues
    ]
    open_questions = [
        {
            "venue_id": venue["id"],
            "name_zh": venue["name_zh"],
            "name_en_official": venue["name_en_official"],
            "open_questions": venue["open_questions"],
        }
        for venue in venues
        if venue["open_questions"]
    ]
    return {"venues": derived_venues, "open_questions": open_questions}


def write_derived_indexes(root: Path) -> list[Path]:
    paths = workspace_paths(root)
    derived = build_derived_indexes(root)
    generated_at = date.today().isoformat()

    venues_path = paths["derived"] / "venues-index.json"
    open_questions_path = paths["derived"] / "open-questions.json"

    write_json_file(
        venues_path,
        {
            "generated_at": generated_at,
            "venues": derived["venues"],
        },
    )
    write_json_file(
        open_questions_path,
        {
            "generated_at": generated_at,
            "items": derived["open_questions"],
        },
    )
    return [venues_path, open_questions_path]
