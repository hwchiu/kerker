from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

SOURCE_TYPES = {
    "official",
    "platform_agency",
    "editorial_case_study",
    "social_inspiration",
}

EVIDENCE_CATEGORIES = {
    "pricing",
    "capacity",
    "rain_backup",
    "photos",
    "restrictions",
    "accommodation",
    "transport",
}


def _as_record(record: dict[str, Any], kind: str) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError(f"{kind} must be a dictionary")
    return deepcopy(record)


def _require_keys(record: dict[str, Any], required: set[str], kind: str) -> None:
    missing = sorted(field for field in required if field not in record)
    if missing:
        raise ValueError(f"{kind} missing required fields: {', '.join(missing)}")


def _require_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _require_string_list(value: Any, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of strings")
    cleaned = [_require_non_empty_string(item, field) for item in value]
    if not allow_empty and not cleaned:
        raise ValueError(f"{field} must not be empty")
    return cleaned


def _require_iso_date(value: Any, field: str) -> str:
    text = _require_non_empty_string(value, field)
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid ISO date") from exc
    return parsed.isoformat()


def _optional_iso_date(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return _require_iso_date(value, field)


def _require_choice(value: Any, field: str, allowed: set[str]) -> str:
    text = _require_non_empty_string(value, field)
    if text not in allowed:
        raise ValueError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    return text


def validate_source_record(record: dict[str, Any]) -> dict[str, Any]:
    candidate = _as_record(record, "source record")
    _require_keys(
        candidate,
        {
            "source_id",
            "venue_id",
            "source_type",
            "source_name",
            "source_url",
            "captured_at",
            "content_date_if_known",
            "language",
            "evidence_categories",
            "reliability_notes",
            "raw_excerpt_summary",
        },
        "source record",
    )

    candidate["source_id"] = _require_non_empty_string(candidate["source_id"], "source_id")
    candidate["venue_id"] = _require_non_empty_string(candidate["venue_id"], "venue_id")
    candidate["source_type"] = _require_choice(
        candidate["source_type"],
        "source_type",
        SOURCE_TYPES,
    )
    candidate["source_name"] = _require_non_empty_string(candidate["source_name"], "source_name")
    candidate["source_url"] = _require_non_empty_string(candidate["source_url"], "source_url")
    candidate["captured_at"] = _require_iso_date(candidate["captured_at"], "captured_at")
    candidate["content_date_if_known"] = _optional_iso_date(
        candidate["content_date_if_known"],
        "content_date_if_known",
    )
    candidate["language"] = _require_non_empty_string(candidate["language"], "language")
    candidate["evidence_categories"] = _require_string_list(
        candidate["evidence_categories"],
        "evidence_categories",
    )
    unknown_categories = sorted(set(candidate["evidence_categories"]) - EVIDENCE_CATEGORIES)
    if unknown_categories:
        raise ValueError(
            "evidence_categories contains unsupported values: "
            + ", ".join(unknown_categories)
        )
    candidate["reliability_notes"] = _require_non_empty_string(
        candidate["reliability_notes"],
        "reliability_notes",
    )
    candidate["raw_excerpt_summary"] = _require_non_empty_string(
        candidate["raw_excerpt_summary"],
        "raw_excerpt_summary",
    )
    return candidate


IMAGE_TYPES = {
    "official_wedding_gallery",
    "official_hotel_gallery",
    "real_wedding_feature",
    "platform_listing_gallery",
    "blog_feature",
    "press_feature",
    "social_post",
}

SCENE_TAGS = {
    "water-platform",
    "chapel-interior",
    "chapel-exterior",
    "cliffside-ceremony",
    "beach-ceremony",
    "garden-reception",
    "ballroom-reception",
    "jungle-view",
    "guest-seating",
    "floral-setup",
    "entrance-procession",
    "night-view",
    "room",
    "public-area",
    "arrival-flow",
    "rain-backup-space",
}

PHOTO_AUTHENTICITY = {"official_promotional", "real_wedding", "unknown"}
PHOTO_COVERAGE_TYPES = {"single_image", "small_gallery", "large_gallery", "document_embedded"}
DECISION_VALUES = {"high", "medium", "low"}
PHOTO_COVERAGE_LEVELS = {"high", "medium", "low", "unknown"}


def validate_photo_record(record: dict[str, Any]) -> dict[str, Any]:
    candidate = _as_record(record, "photo record")
    _require_keys(
        candidate,
        {
            "photo_entry_id",
            "venue_id",
            "source_id",
            "page_url",
            "image_url_or_gallery_url",
            "image_type",
            "scene_tags",
            "authenticity",
            "coverage_type",
            "decision_value",
            "decision_notes",
        },
        "photo record",
    )

    candidate["photo_entry_id"] = _require_non_empty_string(candidate["photo_entry_id"], "photo_entry_id")
    candidate["venue_id"] = _require_non_empty_string(candidate["venue_id"], "venue_id")
    candidate["source_id"] = _require_non_empty_string(candidate["source_id"], "source_id")
    candidate["page_url"] = _require_non_empty_string(candidate["page_url"], "page_url")
    candidate["image_url_or_gallery_url"] = _require_non_empty_string(
        candidate["image_url_or_gallery_url"],
        "image_url_or_gallery_url",
    )
    candidate["image_type"] = _require_choice(candidate["image_type"], "image_type", IMAGE_TYPES)
    candidate["scene_tags"] = _require_string_list(candidate["scene_tags"], "scene_tags")
    unknown_tags = sorted(set(candidate["scene_tags"]) - SCENE_TAGS)
    if unknown_tags:
        raise ValueError(f"scene_tags contains unsupported values: {', '.join(unknown_tags)}")
    candidate["authenticity"] = _require_choice(
        candidate["authenticity"],
        "authenticity",
        PHOTO_AUTHENTICITY,
    )
    candidate["coverage_type"] = _require_choice(
        candidate["coverage_type"],
        "coverage_type",
        PHOTO_COVERAGE_TYPES,
    )
    candidate["decision_value"] = _require_choice(
        candidate["decision_value"],
        "decision_value",
        DECISION_VALUES,
    )
    candidate["decision_notes"] = _require_non_empty_string(
        candidate["decision_notes"],
        "decision_notes",
    )
    return candidate


def _coverage_level(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "unknown"
    high_count = sum(1 for entry in entries if entry["decision_value"] == "high")
    medium_count = sum(1 for entry in entries if entry["decision_value"] == "medium")
    low_count = sum(1 for entry in entries if entry["decision_value"] == "low")
    if high_count >= 2 or (high_count >= 1 and medium_count >= 1):
        return "high"
    if high_count >= 1 or medium_count >= 1 or low_count >= 2:
        return "medium"
    return "low"


def summarize_photo_coverage(photo_entries: list[dict[str, Any]]) -> dict[str, str]:
    ceremony_tags = {
        "water-platform",
        "chapel-interior",
        "chapel-exterior",
        "cliffside-ceremony",
        "beach-ceremony",
    }
    reception_tags = {
        "garden-reception",
        "ballroom-reception",
        "guest-seating",
        "night-view",
        "floral-setup",
    }
    rain_backup_tags = {"rain-backup-space"}
    accommodation_tags = {"room", "public-area", "arrival-flow"}

    def matching_entries(tags: set[str]) -> list[dict[str, Any]]:
        return [
            entry
            for entry in photo_entries
            if set(entry["scene_tags"]) & tags
        ]

    coverage = {
        "photo_coverage_ceremony": _coverage_level(matching_entries(ceremony_tags)),
        "photo_coverage_reception": _coverage_level(matching_entries(reception_tags)),
        "photo_coverage_rain_backup": _coverage_level(matching_entries(rain_backup_tags)),
        "photo_coverage_accommodation": _coverage_level(matching_entries(accommodation_tags)),
    }

    high_count = sum(1 for value in coverage.values() if value == "high")
    medium_count = sum(1 for value in coverage.values() if value == "medium")
    low_count = sum(1 for value in coverage.values() if value == "low")

    if high_count >= 2:
        coverage["photo_reference_value_overall"] = "high"
    elif high_count >= 1 or medium_count >= 1:
        coverage["photo_reference_value_overall"] = "medium"
    elif low_count >= 1:
        coverage["photo_reference_value_overall"] = "low"
    else:
        coverage["photo_reference_value_overall"] = "unknown"

    return coverage
