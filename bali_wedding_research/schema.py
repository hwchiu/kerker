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
