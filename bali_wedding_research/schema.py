from __future__ import annotations

from copy import deepcopy
from datetime import date
import math
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


VENUE_OPERATOR_TYPES = {"hotel", "resort", "standalone_venue", "villa_estate"}
VENUE_TYPES = {
    "water-platform",
    "chapel",
    "cliffside",
    "beach",
    "lawn",
    "garden",
    "jungle",
    "ballroom",
    "villa-buyout",
    "rooftop",
}
GUEST_SIZE_BANDS = {"2-20", "21-50", "51-80", "81-120", "120+"}
PRICING_STATUSES = {"public_price_available", "quote_required", "unknown"}
PRICE_CONFIDENCE = {"high", "medium", "low"}
PRICE_RISK_LEVELS = {"low", "medium", "high"}
RAIN_BACKUP_STATUSES = {"strong", "medium", "weak", "unknown"}
TRAFFIC_RISK_LEVELS = {"low", "medium", "high", "unknown"}
ACCOMMODATION_FITS = {"one_stop", "workable_with_shuttles", "fragmented", "unknown"}
RESTRICTION_LEVELS = {"low", "medium", "high", "unknown"}
DATA_COMPLETENESS = {"deep_complete", "comparable_core_complete", "initial_capture_only"}
RESEARCH_STATUSES = {
    "candidate",
    "record_created",
    "deep_research_complete",
    "needs_price_followup",
    "needs_photo_followup",
}
DATA_FRESHNESS = {"recent", "possibly_outdated", "clearly_outdated"}
PRICE_BANDS = {"budget", "midrange", "premium", "luxury", "ultra_luxury"}


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _require_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _require_number_or_none(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number or null")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{field} must be a finite number or null")
    if number < 0:
        raise ValueError(f"{field} must be zero or greater")
    return number


def normalize_price_band(starting_usd: float | None) -> str | None:
    if starting_usd is None:
        return None
    if starting_usd < 3000:
        return "budget"
    if starting_usd < 6000:
        return "midrange"
    if starting_usd < 10000:
        return "premium"
    if starting_usd < 18000:
        return "luxury"
    return "ultra_luxury"


def validate_price_entry(entry: dict[str, Any]) -> dict[str, Any]:
    candidate = _as_record(entry, "price entry")
    _require_keys(
        candidate,
        {
            "label",
            "currency",
            "amount_min",
            "amount_max",
            "pricing_year",
            "includes_stay",
            "includes_decoration",
            "includes_dinner",
            "includes_tax_service",
            "conditions_text",
            "confidence",
        },
        "price entry",
    )

    candidate["label"] = _require_non_empty_string(candidate["label"], "label")
    candidate["currency"] = _require_non_empty_string(candidate["currency"], "currency").upper()
    candidate["amount_min"] = _require_number_or_none(candidate["amount_min"], "amount_min")
    candidate["amount_max"] = _require_number_or_none(candidate["amount_max"], "amount_max")
    if candidate["amount_min"] is None and candidate["amount_max"] is None:
        raise ValueError("price entry must define amount_min or amount_max")
    if (
        candidate["amount_min"] is not None
        and candidate["amount_max"] is not None
        and candidate["amount_min"] > candidate["amount_max"]
    ):
        raise ValueError("amount_min must be less than or equal to amount_max")
    candidate["pricing_year"] = _require_int(candidate["pricing_year"], "pricing_year")
    candidate["includes_stay"] = _require_bool(candidate["includes_stay"], "includes_stay")
    candidate["includes_decoration"] = _require_bool(
        candidate["includes_decoration"],
        "includes_decoration",
    )
    candidate["includes_dinner"] = _require_bool(candidate["includes_dinner"], "includes_dinner")
    candidate["includes_tax_service"] = _require_bool(
        candidate["includes_tax_service"],
        "includes_tax_service",
    )
    candidate["conditions_text"] = _require_non_empty_string(
        candidate["conditions_text"],
        "conditions_text",
    )
    candidate["confidence"] = _require_choice(
        candidate["confidence"],
        "confidence",
        PRICE_CONFIDENCE,
    )
    return candidate


def _public_starting_price_usd(price_entries: list[dict[str, Any]]) -> float | None:
    usd_values = [
        entry["amount_min"]
        for entry in price_entries
        if entry["currency"] == "USD" and entry["amount_min"] is not None
    ]
    if not usd_values:
        return None
    return min(usd_values)


def _derived_price_risk(pricing_status: str, price_entries: list[dict[str, Any]]) -> str:
    if pricing_status != "public_price_available" or not price_entries:
        return "high"
    if _public_starting_price_usd(price_entries) is None:
        return "high"
    if all(entry["confidence"] == "low" for entry in price_entries):
        return "medium"
    return "low"


def validate_venue_record(record: dict[str, Any]) -> dict[str, Any]:
    candidate = _as_record(record, "venue record")
    _require_keys(
        candidate,
        {
            "id",
            "name_zh",
            "name_en_official",
            "brand_or_group",
            "venue_operator_type",
            "is_standalone",
            "region",
            "subarea",
            "official_website",
            "maps_url",
            "address_text",
            "venue_types",
            "primary_visual_identity",
            "ceremony_space_types",
            "reception_space_types",
            "supports_ceremony_only",
            "supports_ceremony_and_dinner",
            "supports_buyout",
            "supports_micro_wedding",
            "guest_capacity_ceremony_min",
            "guest_capacity_ceremony_max",
            "guest_capacity_dinner_min",
            "guest_capacity_dinner_max",
            "recommended_guest_size_band",
            "pricing_status",
            "price_entries",
            "price_summary_text",
            "price_risk_level",
            "rain_backup_status",
            "has_indoor_backup",
            "has_covered_backup",
            "backup_space_description",
            "backup_quality_notes",
            "weather_exposure_notes",
            "airport_drive_time_minutes_estimate",
            "transport_notes",
            "traffic_risk_level",
            "onsite_accommodation_available",
            "onsite_room_inventory_notes",
            "nearby_accommodation_notes",
            "accommodation_fit",
            "guest_mobility_notes",
            "restriction_level",
            "noise_cutoff_notes",
            "external_vendor_policy",
            "minimum_stay_requirement_notes",
            "minimum_spend_notes",
            "drone_policy_notes",
            "family_child_notes",
            "religious_or_space_use_notes",
            "operational_constraints_notes",
            "style_tags",
            "price_band_normalized",
            "best_for",
            "not_ideal_for",
            "key_strengths",
            "key_risks",
            "data_completeness",
            "research_status",
            "last_verified_at",
            "data_freshness",
            "open_questions",
            "source_ids",
            "photo_index_id",
        },
        "venue record",
    )

    candidate["id"] = _require_non_empty_string(candidate["id"], "id")
    candidate["name_zh"] = _require_non_empty_string(candidate["name_zh"], "name_zh")
    candidate["name_en_official"] = _require_non_empty_string(
        candidate["name_en_official"],
        "name_en_official",
    )
    candidate["brand_or_group"] = _require_non_empty_string(
        candidate["brand_or_group"],
        "brand_or_group",
    )
    candidate["venue_operator_type"] = _require_choice(
        candidate["venue_operator_type"],
        "venue_operator_type",
        VENUE_OPERATOR_TYPES,
    )
    candidate["is_standalone"] = _require_bool(candidate["is_standalone"], "is_standalone")
    candidate["region"] = _require_non_empty_string(candidate["region"], "region")
    candidate["subarea"] = _require_non_empty_string(candidate["subarea"], "subarea")
    candidate["official_website"] = _require_non_empty_string(
        candidate["official_website"],
        "official_website",
    )
    candidate["maps_url"] = _require_non_empty_string(candidate["maps_url"], "maps_url")
    candidate["address_text"] = _require_non_empty_string(candidate["address_text"], "address_text")
    candidate["venue_types"] = _require_string_list(candidate["venue_types"], "venue_types")
    if sorted(set(candidate["venue_types"]) - VENUE_TYPES):
        raise ValueError("venue_types contains unsupported values")
    candidate["primary_visual_identity"] = _require_non_empty_string(
        candidate["primary_visual_identity"],
        "primary_visual_identity",
    )
    candidate["ceremony_space_types"] = _require_string_list(
        candidate["ceremony_space_types"],
        "ceremony_space_types",
    )
    candidate["reception_space_types"] = _require_string_list(
        candidate["reception_space_types"],
        "reception_space_types",
    )
    candidate["supports_ceremony_only"] = _require_bool(
        candidate["supports_ceremony_only"],
        "supports_ceremony_only",
    )
    candidate["supports_ceremony_and_dinner"] = _require_bool(
        candidate["supports_ceremony_and_dinner"],
        "supports_ceremony_and_dinner",
    )
    candidate["supports_buyout"] = _require_bool(candidate["supports_buyout"], "supports_buyout")
    candidate["supports_micro_wedding"] = _require_bool(
        candidate["supports_micro_wedding"],
        "supports_micro_wedding",
    )
    candidate["guest_capacity_ceremony_min"] = _require_int(
        candidate["guest_capacity_ceremony_min"],
        "guest_capacity_ceremony_min",
    )
    candidate["guest_capacity_ceremony_max"] = _require_int(
        candidate["guest_capacity_ceremony_max"],
        "guest_capacity_ceremony_max",
    )
    candidate["guest_capacity_dinner_min"] = _require_int(
        candidate["guest_capacity_dinner_min"],
        "guest_capacity_dinner_min",
    )
    candidate["guest_capacity_dinner_max"] = _require_int(
        candidate["guest_capacity_dinner_max"],
        "guest_capacity_dinner_max",
    )
    candidate["recommended_guest_size_band"] = _require_choice(
        candidate["recommended_guest_size_band"],
        "recommended_guest_size_band",
        GUEST_SIZE_BANDS,
    )
    candidate["pricing_status"] = _require_choice(
        candidate["pricing_status"],
        "pricing_status",
        PRICING_STATUSES,
    )
    if not isinstance(candidate["price_entries"], list):
        raise ValueError("price_entries must be a list")
    candidate["price_entries"] = [validate_price_entry(entry) for entry in candidate["price_entries"]]
    candidate["price_summary_text"] = _require_non_empty_string(
        candidate["price_summary_text"],
        "price_summary_text",
    )
    candidate["rain_backup_status"] = _require_choice(
        candidate["rain_backup_status"],
        "rain_backup_status",
        RAIN_BACKUP_STATUSES,
    )
    candidate["has_indoor_backup"] = _require_bool(
        candidate["has_indoor_backup"],
        "has_indoor_backup",
    )
    candidate["has_covered_backup"] = _require_bool(
        candidate["has_covered_backup"],
        "has_covered_backup",
    )
    candidate["backup_space_description"] = _require_non_empty_string(
        candidate["backup_space_description"],
        "backup_space_description",
    )
    candidate["backup_quality_notes"] = _require_non_empty_string(
        candidate["backup_quality_notes"],
        "backup_quality_notes",
    )
    candidate["weather_exposure_notes"] = _require_non_empty_string(
        candidate["weather_exposure_notes"],
        "weather_exposure_notes",
    )
    candidate["airport_drive_time_minutes_estimate"] = _require_int(
        candidate["airport_drive_time_minutes_estimate"],
        "airport_drive_time_minutes_estimate",
    )
    candidate["transport_notes"] = _require_non_empty_string(
        candidate["transport_notes"],
        "transport_notes",
    )
    candidate["traffic_risk_level"] = _require_choice(
        candidate["traffic_risk_level"],
        "traffic_risk_level",
        TRAFFIC_RISK_LEVELS,
    )
    candidate["onsite_accommodation_available"] = _require_bool(
        candidate["onsite_accommodation_available"],
        "onsite_accommodation_available",
    )
    candidate["onsite_room_inventory_notes"] = _require_non_empty_string(
        candidate["onsite_room_inventory_notes"],
        "onsite_room_inventory_notes",
    )
    candidate["nearby_accommodation_notes"] = _require_non_empty_string(
        candidate["nearby_accommodation_notes"],
        "nearby_accommodation_notes",
    )
    candidate["accommodation_fit"] = _require_choice(
        candidate["accommodation_fit"],
        "accommodation_fit",
        ACCOMMODATION_FITS,
    )
    candidate["guest_mobility_notes"] = _require_non_empty_string(
        candidate["guest_mobility_notes"],
        "guest_mobility_notes",
    )
    candidate["restriction_level"] = _require_choice(
        candidate["restriction_level"],
        "restriction_level",
        RESTRICTION_LEVELS,
    )
    candidate["noise_cutoff_notes"] = _require_non_empty_string(
        candidate["noise_cutoff_notes"],
        "noise_cutoff_notes",
    )
    candidate["external_vendor_policy"] = _require_non_empty_string(
        candidate["external_vendor_policy"],
        "external_vendor_policy",
    )
    candidate["minimum_stay_requirement_notes"] = _require_non_empty_string(
        candidate["minimum_stay_requirement_notes"],
        "minimum_stay_requirement_notes",
    )
    candidate["minimum_spend_notes"] = _require_non_empty_string(
        candidate["minimum_spend_notes"],
        "minimum_spend_notes",
    )
    candidate["drone_policy_notes"] = _require_non_empty_string(
        candidate["drone_policy_notes"],
        "drone_policy_notes",
    )
    candidate["family_child_notes"] = _require_non_empty_string(
        candidate["family_child_notes"],
        "family_child_notes",
    )
    candidate["religious_or_space_use_notes"] = _require_non_empty_string(
        candidate["religious_or_space_use_notes"],
        "religious_or_space_use_notes",
    )
    candidate["operational_constraints_notes"] = _require_non_empty_string(
        candidate["operational_constraints_notes"],
        "operational_constraints_notes",
    )
    candidate["style_tags"] = _require_string_list(candidate["style_tags"], "style_tags")
    candidate["best_for"] = _require_string_list(candidate["best_for"], "best_for")
    candidate["not_ideal_for"] = _require_string_list(candidate["not_ideal_for"], "not_ideal_for")
    candidate["key_strengths"] = _require_string_list(candidate["key_strengths"], "key_strengths")
    candidate["key_risks"] = _require_string_list(candidate["key_risks"], "key_risks")
    candidate["data_completeness"] = _require_choice(
        candidate["data_completeness"],
        "data_completeness",
        DATA_COMPLETENESS,
    )
    candidate["research_status"] = _require_choice(
        candidate["research_status"],
        "research_status",
        RESEARCH_STATUSES,
    )
    candidate["last_verified_at"] = _require_iso_date(
        candidate["last_verified_at"],
        "last_verified_at",
    )
    candidate["data_freshness"] = _require_choice(
        candidate["data_freshness"],
        "data_freshness",
        DATA_FRESHNESS,
    )
    candidate["open_questions"] = _require_string_list(
        candidate["open_questions"],
        "open_questions",
        allow_empty=True,
    )
    candidate["source_ids"] = _require_string_list(candidate["source_ids"], "source_ids")
    duplicate_source_ids = sorted(
        {
            source_id
            for source_id in candidate["source_ids"]
            if candidate["source_ids"].count(source_id) > 1
        }
    )
    if duplicate_source_ids:
        raise ValueError(
            "source_ids must not contain duplicates: " + ", ".join(duplicate_source_ids)
        )
    candidate["photo_index_id"] = _require_non_empty_string(
        candidate["photo_index_id"],
        "photo_index_id",
    )

    if candidate["pricing_status"] == "unknown" and candidate["price_entries"]:
        raise ValueError("pricing_status=unknown must not carry public price entries")
    if (
        candidate["pricing_status"] == "public_price_available"
        and not candidate["price_entries"]
    ):
        raise ValueError(
            "pricing_status=public_price_available requires at least one public price entry"
        )

    public_price = _public_starting_price_usd(candidate["price_entries"])
    expected_band = normalize_price_band(public_price)
    expected_risk = _derived_price_risk(candidate["pricing_status"], candidate["price_entries"])

    if candidate["pricing_status"] == "quote_required" and candidate["price_entries"]:
        raise ValueError("quote_required venues must not carry public price entries")
    if candidate["pricing_status"] == "quote_required" and expected_risk != "high":
        raise ValueError("quote_required venues must be high price risk")
    if candidate["price_band_normalized"] is not None:
        candidate["price_band_normalized"] = _require_choice(
            candidate["price_band_normalized"],
            "price_band_normalized",
            PRICE_BANDS,
        )
    candidate["price_band_normalized"] = expected_band
    if candidate["price_risk_level"] != expected_risk:
        raise ValueError(
            f"price_risk_level must be {expected_risk} for pricing_status={candidate['pricing_status']}"
        )

    return candidate
