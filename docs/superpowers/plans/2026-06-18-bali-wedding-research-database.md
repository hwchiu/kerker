# Bali Wedding Venue Research Database Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python 3.12 research-data pipeline that validates Bali wedding venue records, derives search indexes, and writes venue note files that a later local website can consume directly.

**Architecture:** Use a standard-library Python package to own workspace paths, JSON schema validation, seed deduplication, derived-index generation, and note rendering. Keep source-of-truth venue, source, and photo files as plain JSON under `data/`, then generate website-ready JSON under `data/derived/` and human-readable markdown under `content/venue-notes/`.

**Tech Stack:** Python 3.12, standard library (`argparse`, `copy`, `datetime`, `json`, `pathlib`, `re`, `unittest`)

---

## File Structure

- Create: `pyproject.toml`
- Create: `bali_wedding_research/__init__.py`
- Create: `bali_wedding_research/__main__.py`
- Create: `bali_wedding_research/paths.py`
- Create: `bali_wedding_research/schema.py`
- Create: `bali_wedding_research/seed_registry.py`
- Create: `bali_wedding_research/io.py`
- Create: `bali_wedding_research/derive.py`
- Create: `bali_wedding_research/notes.py`
- Create: `bali_wedding_research/cli.py`
- Create: `tests/__init__.py`
- Create: `tests/test_paths.py`
- Create: `tests/test_source_schema.py`
- Create: `tests/test_photo_schema.py`
- Create: `tests/test_venue_schema.py`
- Create: `tests/test_seed_registry.py`
- Create: `tests/test_derive.py`
- Create: `tests/test_cli.py`
- Create: `tests/test_notes.py`
- Create: `tests/test_workspace_flow.py`
- Create: `tests/sample_data.py`

### File Responsibilities

- `pyproject.toml` declares the Python contract for the repository.
- `bali_wedding_research/paths.py` centralizes directory names so the data layout cannot drift.
- `bali_wedding_research/schema.py` validates and normalizes source, photo, price, and venue JSON records.
- `bali_wedding_research/seed_registry.py` merges candidate venue aliases into canonical seed entries.
- `bali_wedding_research/io.py` loads and saves JSON and validates cross-file references.
- `bali_wedding_research/derive.py` builds `data/derived/venues-index.json` and `data/derived/open-questions.json`.
- `bali_wedding_research/notes.py` renders `content/venue-notes/<venue-id>.md`.
- `bali_wedding_research/cli.py` exposes `init-workspace`, `validate`, `build-derived`, and `build-notes`.
- `tests/sample_data.py` provides reusable synthetic records for integration tests without pretending to be production research data.

### Task 1: Bootstrap Repository Layout

**Files:**
- Create: `pyproject.toml`
- Create: `bali_wedding_research/__init__.py`
- Create: `bali_wedding_research/paths.py`
- Create: `tests/__init__.py`
- Test: `tests/test_paths.py`

- [ ] **Step 1: Write the failing path-layout test**

```python
import tempfile
import unittest
from pathlib import Path

from bali_wedding_research.paths import ensure_workspace_layout, workspace_paths


class WorkspacePathsTest(unittest.TestCase):
    def test_workspace_paths_points_to_expected_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = workspace_paths(root)

            self.assertEqual(paths["root"], root.resolve())
            self.assertEqual(paths["venues"], root / "data" / "venues")
            self.assertEqual(paths["photos"], root / "data" / "photos")
            self.assertEqual(paths["sources"], root / "data" / "sources")
            self.assertEqual(paths["seeds"], root / "data" / "seeds")
            self.assertEqual(paths["derived"], root / "data" / "derived")
            self.assertEqual(paths["notes"], root / "content" / "venue-notes")

    def test_ensure_workspace_layout_creates_all_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            created = ensure_workspace_layout(root)

            self.assertEqual(
                created,
                [
                    root / "data" / "venues",
                    root / "data" / "photos",
                    root / "data" / "sources",
                    root / "data" / "seeds",
                    root / "data" / "derived",
                    root / "content" / "venue-notes",
                ],
            )
            self.assertTrue(all(path.exists() for path in created))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_paths -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bali_wedding_research'`

- [ ] **Step 3: Write the minimal implementation**

`pyproject.toml`
```toml
[project]
name = "bali-wedding-research"
version = "0.1.0"
description = "Structured Bali wedding venue research database"
requires-python = ">=3.12"
```

`bali_wedding_research/__init__.py`
```python
"""Bali wedding venue research database tools."""
```

`tests/__init__.py`
```python
"""Test package for Bali wedding research."""
```

`bali_wedding_research/paths.py`
```python
from __future__ import annotations

from pathlib import Path


def workspace_paths(root: Path) -> dict[str, Path]:
    resolved_root = root.resolve()
    return {
        "root": resolved_root,
        "venues": resolved_root / "data" / "venues",
        "photos": resolved_root / "data" / "photos",
        "sources": resolved_root / "data" / "sources",
        "seeds": resolved_root / "data" / "seeds",
        "derived": resolved_root / "data" / "derived",
        "notes": resolved_root / "content" / "venue-notes",
    }


def ensure_workspace_layout(root: Path) -> list[Path]:
    paths = workspace_paths(root)
    created: list[Path] = []
    for key in ("venues", "photos", "sources", "seeds", "derived", "notes"):
        directory = paths[key]
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)
    return created
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_paths -v`
Expected: PASS with `Ran 2 tests`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml bali_wedding_research/__init__.py bali_wedding_research/paths.py tests/__init__.py tests/test_paths.py
git commit -m "chore: bootstrap research workspace layout"
```

### Task 2: Add Source Record Validation

**Files:**
- Create: `bali_wedding_research/schema.py`
- Test: `tests/test_source_schema.py`

- [ ] **Step 1: Write the failing source-schema test**

```python
import unittest

from bali_wedding_research.schema import validate_source_record


class SourceSchemaTest(unittest.TestCase):
    def test_validate_source_record_accepts_valid_source(self) -> None:
        record = {
            "source_id": "ayana-official-weddings",
            "venue_id": "ayana-resort-bali",
            "source_type": "official",
            "source_name": "AYANA Weddings",
            "source_url": "https://example.com/ayana/weddings",
            "captured_at": "2026-06-18",
            "content_date_if_known": "2026-05-20",
            "language": "en",
            "evidence_categories": ["pricing", "photos", "restrictions"],
            "reliability_notes": "Official venue wedding page",
            "raw_excerpt_summary": "Contains package pricing, gallery links, and usage notes",
        }

        validated = validate_source_record(record)

        self.assertEqual(validated["source_type"], "official")
        self.assertEqual(validated["evidence_categories"], ["pricing", "photos", "restrictions"])

    def test_validate_source_record_rejects_unknown_source_type(self) -> None:
        record = {
            "source_id": "bad-source",
            "venue_id": "ayana-resort-bali",
            "source_type": "travel-forum",
            "source_name": "Forum Post",
            "source_url": "https://example.com/forum",
            "captured_at": "2026-06-18",
            "content_date_if_known": None,
            "language": "en",
            "evidence_categories": ["pricing"],
            "reliability_notes": "Unknown source class",
            "raw_excerpt_summary": "Random comments",
        }

        with self.assertRaises(ValueError):
            validate_source_record(record)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_source_schema -v`
Expected: FAIL with `ImportError: cannot import name 'validate_source_record'`

- [ ] **Step 3: Write the minimal implementation**

`bali_wedding_research/schema.py`
```python
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
    date.fromisoformat(text)
    return text


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
    candidate["source_type"] = _require_choice(candidate["source_type"], "source_type", SOURCE_TYPES)
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_source_schema -v`
Expected: PASS with `Ran 2 tests`

- [ ] **Step 5: Commit**

```bash
git add bali_wedding_research/schema.py tests/test_source_schema.py
git commit -m "feat: add source record validation"
```

### Task 3: Add Photo Record Validation And Coverage Rollups

**Files:**
- Modify: `bali_wedding_research/schema.py`
- Test: `tests/test_photo_schema.py`

- [ ] **Step 1: Write the failing photo-schema test**

```python
import unittest

from bali_wedding_research.schema import summarize_photo_coverage, validate_photo_record


class PhotoSchemaTest(unittest.TestCase):
    def test_validate_photo_record_accepts_real_wedding_gallery(self) -> None:
        record = {
            "photo_entry_id": "ayana-gallery-1",
            "venue_id": "ayana-resort-bali",
            "source_id": "ayana-official-weddings",
            "page_url": "https://example.com/ayana/gallery",
            "image_url_or_gallery_url": "https://example.com/images/ayana-1.jpg",
            "image_type": "real_wedding_feature",
            "scene_tags": ["cliffside-ceremony", "guest-seating"],
            "authenticity": "real_wedding",
            "coverage_type": "large_gallery",
            "decision_value": "high",
            "decision_notes": "Shows the ceremony aisle and guest seating scale",
        }

        validated = validate_photo_record(record)

        self.assertEqual(validated["authenticity"], "real_wedding")

    def test_validate_photo_record_rejects_unknown_scene_tag(self) -> None:
        record = {
            "photo_entry_id": "bad-scene",
            "venue_id": "ayana-resort-bali",
            "source_id": "ayana-official-weddings",
            "page_url": "https://example.com/ayana/gallery",
            "image_url_or_gallery_url": "https://example.com/images/ayana-2.jpg",
            "image_type": "official_wedding_gallery",
            "scene_tags": ["dragon-ceremony"],
            "authenticity": "official_promotional",
            "coverage_type": "small_gallery",
            "decision_value": "medium",
            "decision_notes": "Unsupported scene tag",
        }

        with self.assertRaises(ValueError):
            validate_photo_record(record)

    def test_summarize_photo_coverage_scores_relevant_scenes(self) -> None:
        entries = [
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-1",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/1",
                    "image_url_or_gallery_url": "https://example.com/images/1.jpg",
                    "image_type": "real_wedding_feature",
                    "scene_tags": ["cliffside-ceremony"],
                    "authenticity": "real_wedding",
                    "coverage_type": "large_gallery",
                    "decision_value": "high",
                    "decision_notes": "Clear ceremony aisle photo",
                }
            ),
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-2",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/2",
                    "image_url_or_gallery_url": "https://example.com/images/2.jpg",
                    "image_type": "real_wedding_feature",
                    "scene_tags": ["guest-seating", "night-view"],
                    "authenticity": "real_wedding",
                    "coverage_type": "large_gallery",
                    "decision_value": "high",
                    "decision_notes": "Shows reception seating and night ambiance",
                }
            ),
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-3",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/3",
                    "image_url_or_gallery_url": "https://example.com/images/3.jpg",
                    "image_type": "official_hotel_gallery",
                    "scene_tags": ["room"],
                    "authenticity": "official_promotional",
                    "coverage_type": "small_gallery",
                    "decision_value": "low",
                    "decision_notes": "Only one room overview",
                }
            ),
        ]

        coverage = summarize_photo_coverage(entries)

        self.assertEqual(coverage["photo_coverage_ceremony"], "medium")
        self.assertEqual(coverage["photo_coverage_reception"], "medium")
        self.assertEqual(coverage["photo_coverage_accommodation"], "low")
        self.assertEqual(coverage["photo_reference_value_overall"], "medium")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_photo_schema -v`
Expected: FAIL with `ImportError: cannot import name 'summarize_photo_coverage'`

- [ ] **Step 3: Write the minimal implementation**

Add this code to `bali_wedding_research/schema.py` below `validate_source_record`:

```python
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
    if high_count >= 2 or len(entries) >= 4:
        return "high"
    if high_count == 1 or len(entries) >= 2:
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
    elif high_count == 1 or medium_count >= 2:
        coverage["photo_reference_value_overall"] = "medium"
    elif low_count >= 1:
        coverage["photo_reference_value_overall"] = "low"
    else:
        coverage["photo_reference_value_overall"] = "unknown"

    return coverage
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_photo_schema -v`
Expected: PASS with `Ran 3 tests`

- [ ] **Step 5: Commit**

```bash
git add bali_wedding_research/schema.py tests/test_photo_schema.py
git commit -m "feat: add photo record validation and coverage rollups"
```

### Task 4: Add Venue Validation And Price Normalization

**Files:**
- Modify: `bali_wedding_research/schema.py`
- Test: `tests/test_venue_schema.py`

- [ ] **Step 1: Write the failing venue-schema test**

```python
import unittest

from bali_wedding_research.schema import validate_venue_record


class VenueSchemaTest(unittest.TestCase):
    def _base_venue(self) -> dict[str, object]:
        return {
            "id": "ayana-resort-bali",
            "name_zh": "阿雅娜峇里島度假村",
            "name_en_official": "AYANA Resort Bali",
            "brand_or_group": "AYANA Hospitality",
            "venue_operator_type": "resort",
            "is_standalone": False,
            "region": "Jimbaran",
            "subarea": "Ayana Estate",
            "official_website": "https://example.com/ayana",
            "maps_url": "https://maps.example.com/ayana",
            "address_text": "Karang Mas Estate, Jimbaran, Bali",
            "venue_types": ["cliffside", "chapel"],
            "primary_visual_identity": "Cliffside chapel with ocean backdrop",
            "ceremony_space_types": ["chapel", "cliffside-terrace"],
            "reception_space_types": ["garden", "private-dining"],
            "supports_ceremony_only": True,
            "supports_ceremony_and_dinner": True,
            "supports_buyout": False,
            "supports_micro_wedding": True,
            "guest_capacity_ceremony_min": 10,
            "guest_capacity_ceremony_max": 80,
            "guest_capacity_dinner_min": 20,
            "guest_capacity_dinner_max": 120,
            "recommended_guest_size_band": "81-120",
            "pricing_status": "public_price_available",
            "price_entries": [
                {
                    "label": "Cliffside chapel package",
                    "currency": "USD",
                    "amount_min": 8500,
                    "amount_max": None,
                    "pricing_year": 2026,
                    "includes_stay": False,
                    "includes_decoration": True,
                    "includes_dinner": False,
                    "includes_tax_service": False,
                    "conditions_text": "Ceremony package only",
                    "confidence": "high",
                }
            ],
            "price_summary_text": "Public ceremony package starts at USD 8,500",
            "price_risk_level": "low",
            "rain_backup_status": "strong",
            "has_indoor_backup": True,
            "has_covered_backup": True,
            "backup_space_description": "Indoor function room held as weather backup",
            "backup_quality_notes": "Backup keeps sea-facing feel but moves indoors",
            "weather_exposure_notes": "Primary ceremony remains wind exposed",
            "airport_drive_time_minutes_estimate": 25,
            "transport_notes": "Straightforward airport access outside peak traffic",
            "traffic_risk_level": "medium",
            "onsite_accommodation_available": True,
            "onsite_room_inventory_notes": "Large integrated resort inventory",
            "nearby_accommodation_notes": "Additional Jimbaran hotels nearby",
            "accommodation_fit": "one_stop",
            "guest_mobility_notes": "Suitable for guests who prefer minimal transfers",
            "restriction_level": "medium",
            "noise_cutoff_notes": "Outdoor amplified music ends at 22:00",
            "external_vendor_policy": "Outside vendors allowed with coordination",
            "minimum_stay_requirement_notes": "No mandatory buyout for ceremony package",
            "minimum_spend_notes": "Dinner venue may require separate minimum spend",
            "drone_policy_notes": "Subject to weather and resort permission",
            "family_child_notes": "Family-friendly resort",
            "religious_or_space_use_notes": "Chapel is used for symbolic ceremonies",
            "operational_constraints_notes": "Sunset slots book early",
            "style_tags": ["ocean-view", "cliffside", "chapel"],
            "price_band_normalized": None,
            "best_for": ["Guests wanting a resort stay and iconic cliff views"],
            "not_ideal_for": ["Couples needing the lowest possible package price"],
            "key_strengths": ["Integrated stay experience", "Strong visual identity"],
            "key_risks": ["Sunset inventory pressure", "Outdoor wind exposure"],
            "data_completeness": "deep_complete",
            "research_status": "deep_research_complete",
            "last_verified_at": "2026-06-18",
            "data_freshness": "recent",
            "open_questions": [],
            "source_ids": ["ayana-official-weddings"],
            "photo_index_id": "ayana-resort-bali",
        }

    def test_validate_venue_record_normalizes_price_band_for_public_prices(self) -> None:
        validated = validate_venue_record(self._base_venue())

        self.assertEqual(validated["price_band_normalized"], "premium")
        self.assertEqual(validated["price_risk_level"], "low")

    def test_validate_venue_record_requires_high_risk_for_quote_only(self) -> None:
        record = self._base_venue()
        record["pricing_status"] = "quote_required"
        record["price_entries"] = []
        record["price_summary_text"] = "Quote required"
        record["price_risk_level"] = "low"
        record["price_band_normalized"] = None

        with self.assertRaises(ValueError):
            validate_venue_record(record)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_venue_schema -v`
Expected: FAIL with `ImportError: cannot import name 'validate_venue_record'`

- [ ] **Step 3: Write the minimal implementation**

Add this code to `bali_wedding_research/schema.py` below `summarize_photo_coverage`:

```python
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
    if not isinstance(value, int):
        raise ValueError(f"{field} must be an integer")
    return value


def _require_number_or_none(value: Any, field: str) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number or null")
    return float(value)


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
    candidate["currency"] = _require_non_empty_string(candidate["currency"], "currency")
    candidate["amount_min"] = _require_number_or_none(candidate["amount_min"], "amount_min")
    candidate["amount_max"] = _require_number_or_none(candidate["amount_max"], "amount_max")
    if candidate["amount_min"] is None and candidate["amount_max"] is None:
        raise ValueError("price entry must define amount_min or amount_max")
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
    candidate["confidence"] = _require_choice(candidate["confidence"], "confidence", PRICE_CONFIDENCE)
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
    candidate["brand_or_group"] = _require_non_empty_string(candidate["brand_or_group"], "brand_or_group")
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
    candidate["has_indoor_backup"] = _require_bool(candidate["has_indoor_backup"], "has_indoor_backup")
    candidate["has_covered_backup"] = _require_bool(candidate["has_covered_backup"], "has_covered_backup")
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
    candidate["transport_notes"] = _require_non_empty_string(candidate["transport_notes"], "transport_notes")
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
    candidate["last_verified_at"] = _require_iso_date(candidate["last_verified_at"], "last_verified_at")
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
    candidate["photo_index_id"] = _require_non_empty_string(candidate["photo_index_id"], "photo_index_id")

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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_venue_schema -v`
Expected: PASS with `Ran 2 tests`

- [ ] **Step 5: Commit**

```bash
git add bali_wedding_research/schema.py tests/test_venue_schema.py
git commit -m "feat: add venue validation and price normalization"
```

### Task 5: Add Seed Registry Deduplication

**Files:**
- Create: `bali_wedding_research/seed_registry.py`
- Test: `tests/test_seed_registry.py`

- [ ] **Step 1: Write the failing seed-registry test**

```python
import unittest

from bali_wedding_research.seed_registry import merge_seed_registry, slugify_name


class SeedRegistryTest(unittest.TestCase):
    def test_slugify_name_normalizes_spacing_and_case(self) -> None:
        self.assertEqual(slugify_name("AYANA Resort Bali"), "ayana-resort-bali")
        self.assertEqual(slugify_name("The Edge Uluwatu"), "the-edge-uluwatu")

    def test_merge_seed_registry_merges_alias_matches(self) -> None:
        entries = [
            {
                "seed_id": "ayana-resort-bali",
                "name_en": "AYANA Resort Bali",
                "aliases": ["AYANA Bali"],
                "region": "Jimbaran",
                "discovery_urls": ["https://example.com/ayana-official"],
                "status": "candidate",
            },
            {
                "seed_id": "ayana-bali-listing",
                "name_en": "AYANA Bali",
                "aliases": ["AYANA Resort Bali"],
                "region": "Jimbaran",
                "discovery_urls": ["https://example.com/ayana-listing"],
                "status": "candidate",
            },
        ]

        merged = merge_seed_registry(entries)

        self.assertEqual(len(merged), 1)
        self.assertEqual(
            merged[0]["discovery_urls"],
            ["https://example.com/ayana-listing", "https://example.com/ayana-official"],
        )
        self.assertEqual(
            merged[0]["aliases"],
            ["AYANA Bali", "AYANA Resort Bali"],
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_seed_registry -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bali_wedding_research.seed_registry'`

- [ ] **Step 3: Write the minimal implementation**

`bali_wedding_research/seed_registry.py`
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_seed_registry -v`
Expected: PASS with `Ran 2 tests`

- [ ] **Step 5: Commit**

```bash
git add bali_wedding_research/seed_registry.py tests/test_seed_registry.py
git commit -m "feat: add seed registry deduplication"
```

### Task 6: Add Workspace IO And Derived Index Generation

**Files:**
- Create: `bali_wedding_research/io.py`
- Create: `bali_wedding_research/derive.py`
- Create: `tests/sample_data.py`
- Test: `tests/test_derive.py`

- [ ] **Step 1: Write the failing derived-index test**

```python
import json
import tempfile
import unittest
from pathlib import Path

from bali_wedding_research.derive import build_derived_indexes, write_derived_indexes
from bali_wedding_research.io import load_json_file, validate_workspace, write_json_file
from bali_wedding_research.paths import ensure_workspace_layout, workspace_paths
from tests.sample_data import photo_records, source_record, venue_record


class DerivedIndexTest(unittest.TestCase):
    def test_validate_workspace_and_write_derived_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_workspace_layout(root)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            counts = validate_workspace(root)
            self.assertEqual(counts, {"venues": 1, "sources": 1, "photos": 3})

            derived = build_derived_indexes(root)
            self.assertEqual(len(derived["venues"]), 1)
            self.assertEqual(derived["venues"][0]["price_band_normalized"], "premium")
            self.assertEqual(derived["venues"][0]["photo_reference_value_overall"], "high")

            outputs = write_derived_indexes(root)
            self.assertEqual(len(outputs), 2)

            written = load_json_file(paths["derived"] / "venues-index.json")
            self.assertEqual(written["venues"][0]["id"], "example-cliffside-resort")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_derive -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bali_wedding_research.derive'`

- [ ] **Step 3: Write the minimal implementation**

`tests/sample_data.py`
```python
from __future__ import annotations


def source_record() -> dict[str, object]:
    return {
        "source_id": "example-cliffside-official",
        "venue_id": "example-cliffside-resort",
        "source_type": "official",
        "source_name": "Example Cliffside Weddings",
        "source_url": "https://example.com/cliffside/weddings",
        "captured_at": "2026-06-18",
        "content_date_if_known": "2026-05-01",
        "language": "en",
        "evidence_categories": ["pricing", "photos", "restrictions", "accommodation"],
        "reliability_notes": "Synthetic official source for test coverage",
        "raw_excerpt_summary": "Contains pricing, image gallery, and venue constraints",
    }


def photo_records() -> list[dict[str, object]]:
    return [
        {
            "photo_entry_id": "example-photo-1",
            "venue_id": "example-cliffside-resort",
            "source_id": "example-cliffside-official",
            "page_url": "https://example.com/cliffside/gallery/1",
            "image_url_or_gallery_url": "https://example.com/images/1.jpg",
            "image_type": "real_wedding_feature",
            "scene_tags": ["cliffside-ceremony"],
            "authenticity": "real_wedding",
            "coverage_type": "large_gallery",
            "decision_value": "high",
            "decision_notes": "Shows full ceremony setup and aisle width",
        },
        {
            "photo_entry_id": "example-photo-2",
            "venue_id": "example-cliffside-resort",
            "source_id": "example-cliffside-official",
            "page_url": "https://example.com/cliffside/gallery/2",
            "image_url_or_gallery_url": "https://example.com/images/2.jpg",
            "image_type": "real_wedding_feature",
            "scene_tags": ["guest-seating", "night-view"],
            "authenticity": "real_wedding",
            "coverage_type": "large_gallery",
            "decision_value": "high",
            "decision_notes": "Shows dinner seating layout and lighting",
        },
        {
            "photo_entry_id": "example-photo-3",
            "venue_id": "example-cliffside-resort",
            "source_id": "example-cliffside-official",
            "page_url": "https://example.com/cliffside/gallery/3",
            "image_url_or_gallery_url": "https://example.com/images/3.jpg",
            "image_type": "official_hotel_gallery",
            "scene_tags": ["room"],
            "authenticity": "official_promotional",
            "coverage_type": "small_gallery",
            "decision_value": "low",
            "decision_notes": "Single room photo",
        },
    ]


def venue_record() -> dict[str, object]:
    return {
        "id": "example-cliffside-resort",
        "name_zh": "範例懸崖度假村",
        "name_en_official": "Example Cliffside Resort",
        "brand_or_group": "Example Hospitality",
        "venue_operator_type": "resort",
        "is_standalone": False,
        "region": "Uluwatu",
        "subarea": "Southern Ridge",
        "official_website": "https://example.com/cliffside",
        "maps_url": "https://maps.example.com/cliffside",
        "address_text": "Uluwatu, Bali",
        "venue_types": ["cliffside", "chapel"],
        "primary_visual_identity": "Oceanfront cliffside ceremony deck",
        "ceremony_space_types": ["chapel", "cliffside-terrace"],
        "reception_space_types": ["garden", "private-dining"],
        "supports_ceremony_only": True,
        "supports_ceremony_and_dinner": True,
        "supports_buyout": False,
        "supports_micro_wedding": True,
        "guest_capacity_ceremony_min": 10,
        "guest_capacity_ceremony_max": 60,
        "guest_capacity_dinner_min": 20,
        "guest_capacity_dinner_max": 90,
        "recommended_guest_size_band": "81-120",
        "pricing_status": "public_price_available",
        "price_entries": [
            {
                "label": "Cliffside ceremony package",
                "currency": "USD",
                "amount_min": 8500,
                "amount_max": None,
                "pricing_year": 2026,
                "includes_stay": False,
                "includes_decoration": True,
                "includes_dinner": False,
                "includes_tax_service": False,
                "conditions_text": "Ceremony package only",
                "confidence": "high",
            }
        ],
        "price_summary_text": "Public ceremony package starts at USD 8,500",
        "price_risk_level": "low",
        "rain_backup_status": "strong",
        "has_indoor_backup": True,
        "has_covered_backup": True,
        "backup_space_description": "Indoor lounge backup",
        "backup_quality_notes": "Backup maintains sea-facing access",
        "weather_exposure_notes": "Primary deck is wind exposed",
        "airport_drive_time_minutes_estimate": 40,
        "transport_notes": "Traffic slows near sunset hours",
        "traffic_risk_level": "high",
        "onsite_accommodation_available": True,
        "onsite_room_inventory_notes": "Enough rooms for immediate family groups",
        "nearby_accommodation_notes": "Additional cliffside stays require shuttles",
        "accommodation_fit": "workable_with_shuttles",
        "guest_mobility_notes": "Best with arranged transfers for older guests",
        "restriction_level": "medium",
        "noise_cutoff_notes": "Outdoor amplified music ends at 22:00",
        "external_vendor_policy": "External vendors allowed with prior approval",
        "minimum_stay_requirement_notes": "No mandatory buyout",
        "minimum_spend_notes": "Reception minimum spend applies",
        "drone_policy_notes": "Drone use requires venue approval",
        "family_child_notes": "Children allowed with supervision",
        "religious_or_space_use_notes": "Symbolic ceremony focus",
        "operational_constraints_notes": "Popular sunset block fills early",
        "style_tags": ["cliffside", "ocean-view", "chapel"],
        "price_band_normalized": None,
        "best_for": ["Couples prioritizing dramatic cliffside visuals"],
        "not_ideal_for": ["Guests seeking the shortest airport transfer"],
        "key_strengths": ["Strong scenery", "Clear ceremony imagery"],
        "key_risks": ["High traffic risk", "Reception minimum spend"],
        "data_completeness": "deep_complete",
        "research_status": "deep_research_complete",
        "last_verified_at": "2026-06-18",
        "data_freshness": "recent",
        "open_questions": ["Confirm corkage fees for external alcohol"],
        "source_ids": ["example-cliffside-official"],
        "photo_index_id": "example-cliffside-resort",
    }
```

`bali_wedding_research/io.py`
```python
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


def load_workspace_records(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
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
```

`bali_wedding_research/derive.py`
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_derive -v`
Expected: PASS with `Ran 1 test`

- [ ] **Step 5: Commit**

```bash
git add bali_wedding_research/io.py bali_wedding_research/derive.py tests/sample_data.py tests/test_derive.py
git commit -m "feat: add workspace validation and derived indexes"
```

### Task 7: Add CLI Commands For Workspace Operations

**Files:**
- Create: `bali_wedding_research/__main__.py`
- Create: `bali_wedding_research/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing CLI test**

```python
import tempfile
import unittest
from pathlib import Path

from bali_wedding_research.cli import main
from bali_wedding_research.io import write_json_file
from bali_wedding_research.paths import workspace_paths
from tests.sample_data import photo_records, source_record, venue_record


class CliTest(unittest.TestCase):
    def test_init_workspace_creates_expected_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main(["init-workspace", "--root", tmpdir])
            self.assertEqual(exit_code, 0)

            paths = workspace_paths(Path(tmpdir))
            self.assertTrue(paths["venues"].exists())
            self.assertTrue(paths["notes"].exists())

    def test_build_derived_writes_output_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main(["init-workspace", "--root", tmpdir])
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            exit_code = main(["build-derived", "--root", tmpdir])
            self.assertEqual(exit_code, 0)
            self.assertTrue((paths["derived"] / "venues-index.json").exists())
            self.assertTrue((paths["derived"] / "open-questions.json").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_cli -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bali_wedding_research.cli'`

- [ ] **Step 3: Write the minimal implementation**

`bali_wedding_research/cli.py`
```python
from __future__ import annotations

import argparse
from pathlib import Path

from .derive import write_derived_indexes
from .io import validate_workspace
from .paths import ensure_workspace_layout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bali_wedding_research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-workspace")
    init_parser.add_argument("--root", default=".")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--root", default=".")

    derived_parser = subparsers.add_parser("build-derived")
    derived_parser.add_argument("--root", default=".")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)

    if args.command == "init-workspace":
        created = ensure_workspace_layout(root)
        for path in created:
            print(path)
        return 0

    if args.command == "validate":
        counts = validate_workspace(root)
        print(
            f"validated venues={counts['venues']} "
            f"sources={counts['sources']} "
            f"photos={counts['photos']}"
        )
        return 0

    if args.command == "build-derived":
        outputs = write_derived_indexes(root)
        for path in outputs:
            print(path)
        return 0

    parser.error("unsupported command")
    return 2
```

`bali_wedding_research/__main__.py`
```python
from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_cli -v`
Expected: PASS with `Ran 2 tests`

- [ ] **Step 5: Commit**

```bash
git add bali_wedding_research/__main__.py bali_wedding_research/cli.py tests/test_cli.py
git commit -m "feat: add CLI for workspace operations"
```

### Task 8: Add Venue Note Rendering And End-To-End Flow Validation

**Files:**
- Create: `bali_wedding_research/notes.py`
- Modify: `bali_wedding_research/cli.py`
- Modify: `tests/test_cli.py`
- Test: `tests/test_notes.py`
- Test: `tests/test_workspace_flow.py`

- [ ] **Step 1: Write the failing notes and workspace-flow tests**

`tests/test_notes.py`
```python
import tempfile
import unittest
from pathlib import Path

from bali_wedding_research.notes import render_venue_note, write_all_venue_notes
from bali_wedding_research.io import write_json_file
from bali_wedding_research.paths import ensure_workspace_layout, workspace_paths
from tests.sample_data import photo_records, source_record, venue_record


class NotesTest(unittest.TestCase):
    def test_render_venue_note_contains_decision_sections(self) -> None:
        venue = venue_record()
        derived = {
            "id": venue["id"],
            "name_zh": venue["name_zh"],
            "name_en_official": venue["name_en_official"],
            "region": venue["region"],
            "venue_types": venue["venue_types"],
            "pricing_status": venue["pricing_status"],
            "price_band_normalized": "premium",
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
            "source_count": 1,
            "photo_count": 3,
            "photo_coverage_ceremony": "medium",
            "photo_coverage_reception": "medium",
            "photo_coverage_rain_backup": "unknown",
            "photo_coverage_accommodation": "low",
            "photo_reference_value_overall": "medium",
        }

        note = render_venue_note(venue, derived)

        self.assertIn("# 範例懸崖度假村 (Example Cliffside Resort)", note)
        self.assertIn("## 快速判讀", note)
        self.assertIn("## 適合誰", note)
        self.assertIn("## 主要風險", note)

    def test_write_all_venue_notes_creates_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_workspace_layout(root)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            written = write_all_venue_notes(root)

            self.assertEqual(len(written), 1)
            self.assertTrue(written[0].exists())


if __name__ == "__main__":
    unittest.main()
```

`tests/test_workspace_flow.py`
```python
import tempfile
import unittest
from pathlib import Path

from bali_wedding_research.derive import write_derived_indexes
from bali_wedding_research.io import validate_workspace, write_json_file
from bali_wedding_research.notes import write_all_venue_notes
from bali_wedding_research.paths import ensure_workspace_layout, workspace_paths
from tests.sample_data import photo_records, source_record, venue_record


class WorkspaceFlowTest(unittest.TestCase):
    def test_workspace_flow_validates_derives_and_writes_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_workspace_layout(root)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            counts = validate_workspace(root)
            self.assertEqual(counts, {"venues": 1, "sources": 1, "photos": 3})

            write_derived_indexes(root)
            written_notes = write_all_venue_notes(root)

            self.assertEqual(len(written_notes), 1)
            self.assertTrue((paths["derived"] / "venues-index.json").exists())
            self.assertTrue((paths["notes"] / "example-cliffside-resort.md").exists())


if __name__ == "__main__":
    unittest.main()
```

Update `tests/test_cli.py` by appending this test method inside `CliTest`:

```python
    def test_build_notes_writes_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main(["init-workspace", "--root", tmpdir])
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            exit_code = main(["build-notes", "--root", tmpdir])
            self.assertEqual(exit_code, 0)
            self.assertTrue((paths["notes"] / "example-cliffside-resort.md").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_notes tests.test_workspace_flow tests.test_cli -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'bali_wedding_research.notes'`

- [ ] **Step 3: Write the minimal implementation**

`bali_wedding_research/notes.py`
```python
from __future__ import annotations

from pathlib import Path
from typing import Any

from .derive import build_derived_indexes
from .io import load_workspace_records
from .paths import ensure_workspace_layout, workspace_paths


def render_venue_note(venue: dict[str, Any], derived_entry: dict[str, Any]) -> str:
    venue_types = ", ".join(venue["venue_types"])
    best_for = "\n".join(f"- {item}" for item in venue["best_for"])
    not_ideal_for = "\n".join(f"- {item}" for item in venue["not_ideal_for"])
    strengths = "\n".join(f"- {item}" for item in venue["key_strengths"])
    risks = "\n".join(f"- {item}" for item in venue["key_risks"])
    open_questions = (
        "\n".join(f"- {item}" for item in venue["open_questions"])
        if venue["open_questions"]
        else "- 目前沒有公開資料待補問題"
    )

    return (
        f"# {venue['name_zh']} ({venue['name_en_official']})\n\n"
        "## 快速判讀\n"
        f"- 地區：{venue['region']}\n"
        f"- 場地型態：{venue_types}\n"
        f"- 價格狀態：{venue['pricing_status']}\n"
        f"- 價位帶：{derived_entry['price_band_normalized']}\n"
        f"- 雨備強度：{venue['rain_backup_status']}\n"
        f"- 住宿整合：{venue['accommodation_fit']}\n"
        f"- 交通風險：{venue['traffic_risk_level']}\n"
        f"- 照片參考價值：{derived_entry['photo_reference_value_overall']}\n\n"
        "## 適合誰\n"
        f"{best_for}\n\n"
        "## 不適合誰\n"
        f"{not_ideal_for}\n\n"
        "## 主要優勢\n"
        f"{strengths}\n\n"
        "## 主要風險\n"
        f"{risks}\n\n"
        "## 待確認\n"
        f"{open_questions}\n"
    )


def write_all_venue_notes(root: Path) -> list[Path]:
    ensure_workspace_layout(root)
    paths = workspace_paths(root)
    venues, _, _ = load_workspace_records(root)
    derived_lookup = {
        entry["id"]: entry
        for entry in build_derived_indexes(root)["venues"]
    }

    written: list[Path] = []
    for venue in venues:
        target = paths["notes"] / f"{venue['id']}.md"
        target.write_text(
            render_venue_note(venue, derived_lookup[venue["id"]]),
            encoding="utf-8",
        )
        written.append(target)
    return written
```

Update `bali_wedding_research/cli.py` by replacing `build_parser()` and `main()` with:

```python
from .notes import write_all_venue_notes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bali_wedding_research")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-workspace")
    init_parser.add_argument("--root", default=".")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--root", default=".")

    derived_parser = subparsers.add_parser("build-derived")
    derived_parser.add_argument("--root", default=".")

    notes_parser = subparsers.add_parser("build-notes")
    notes_parser.add_argument("--root", default=".")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)

    if args.command == "init-workspace":
        created = ensure_workspace_layout(root)
        for path in created:
            print(path)
        return 0

    if args.command == "validate":
        counts = validate_workspace(root)
        print(
            f"validated venues={counts['venues']} "
            f"sources={counts['sources']} "
            f"photos={counts['photos']}"
        )
        return 0

    if args.command == "build-derived":
        outputs = write_derived_indexes(root)
        for path in outputs:
            print(path)
        return 0

    if args.command == "build-notes":
        outputs = write_all_venue_notes(root)
        for path in outputs:
            print(path)
        return 0

    parser.error("unsupported command")
    return 2
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_notes tests.test_workspace_flow tests.test_cli -v`
Expected: PASS with `Ran 6 tests`

- [ ] **Step 5: Commit**

```bash
git add bali_wedding_research/notes.py bali_wedding_research/cli.py tests/test_cli.py tests/test_notes.py tests/test_workspace_flow.py
git commit -m "feat: add venue note rendering and end-to-end workflow checks"
```

### Task 9: Persist Seed Registry Through The CLI

**Files:**
- Modify: `bali_wedding_research/cli.py`
- Modify: `tests/test_cli.py`
- Test: `tests/test_cli.py`
- [ ] **Step 1: Write the failing seed-merge CLI test**

Append this test method inside `CliTest` in `tests/test_cli.py`:

```python
    def test_merge_seeds_writes_canonical_seed_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            main(["init-workspace", "--root", tmpdir])
            paths = workspace_paths(root)

            raw_a = root / "seed-a.json"
            raw_b = root / "seed-b.json"

            write_json_file(
                raw_a,
                [
                    {
                        "seed_id": "example-cliffside-resort",
                        "name_en": "Example Cliffside Resort",
                        "aliases": ["Example Cliffside"],
                        "region": "Uluwatu",
                        "discovery_urls": ["https://example.com/seed-a"],
                        "status": "candidate",
                    }
                ],
            )
            write_json_file(
                raw_b,
                [
                    {
                        "seed_id": "example-cliffside-listing",
                        "name_en": "Example Cliffside",
                        "aliases": ["Example Cliffside Resort"],
                        "region": "Uluwatu",
                        "discovery_urls": ["https://example.com/seed-b"],
                        "status": "candidate",
                    }
                ],
            )

            exit_code = main(
                [
                    "merge-seeds",
                    "--root",
                    tmpdir,
                    "--input",
                    str(raw_a),
                    "--input",
                    str(raw_b),
                ]
            )

            self.assertEqual(exit_code, 0)
            merged_path = paths["seeds"] / "venue-seeds.json"
            self.assertTrue(merged_path.exists())
            merged = load_json_file(merged_path)
            self.assertEqual(len(merged), 1)
            self.assertEqual(
                merged[0]["discovery_urls"],
                ["https://example.com/seed-a", "https://example.com/seed-b"],
            )
```

Update the import line in `tests/test_cli.py` from:

```python
from bali_wedding_research.io import write_json_file
```

to:

```python
from bali_wedding_research.io import load_json_file, write_json_file
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_cli -v`
Expected: FAIL because `merge-seeds` is not yet a supported CLI command

- [ ] **Step 3: Write the minimal implementation**

Update `bali_wedding_research/cli.py` by adding these imports near the top:

```python
from .io import load_json_file, write_json_file
from .seed_registry import merge_seed_registry
from .paths import workspace_paths
```

Update `build_parser()` in `bali_wedding_research/cli.py` by adding:

```python
    seed_parser = subparsers.add_parser("merge-seeds")
    seed_parser.add_argument("--root", default=".")
    seed_parser.add_argument("--input", action="append", required=True)
```

Update `main()` in `bali_wedding_research/cli.py` by adding this branch before the final `parser.error(...)`:

```python
    if args.command == "merge-seeds":
        paths = workspace_paths(root)
        raw_entries: list[dict[str, object]] = []
        for input_path in args.input:
            payload = load_json_file(Path(input_path))
            if isinstance(payload, list):
                raw_entries.extend(payload)
            else:
                raw_entries.append(payload)
        merged = merge_seed_registry(raw_entries)
        output_path = paths["seeds"] / "venue-seeds.json"
        write_json_file(output_path, merged)
        print(output_path)
        return 0
```

- [ ] **Step 4: Run the CLI test suite**

Run: `python3 -m unittest tests.test_cli -v`
Expected: PASS with `Ran 4 tests`

- [ ] **Step 5: Commit**

```bash
git add bali_wedding_research/cli.py tests/test_cli.py
git commit -m "feat: persist merged seed registry through CLI"
```

## Self-Review Checklist

### Spec Coverage

- Source tracking: covered by Tasks 2, 6, and 9.
- Photo indexing and usefulness scoring: covered by Task 3.
- Venue canonical schema, pricing, rain backup, transport, accommodation, and restriction fields: covered by Task 4.
- Seed registry and alias deduplication: covered by Tasks 5 and 9.
- Derived website-ready JSON: covered by Task 6.
- Human-readable venue notes: covered by Task 8.
- Cross-record integrity and unknown/contradiction-safe validation: covered by Tasks 4 and 6.

### Placeholder Scan

- No unfinished placeholder markers remain anywhere in the plan.
- Every code-writing step includes concrete file contents or patch content.
- Every verification step includes a concrete command and expected result.

### Type Consistency

- `validate_source_record`, `validate_photo_record`, `validate_venue_record`, `validate_workspace`, `build_derived_indexes`, and `write_all_venue_notes` are named consistently across tasks.
- `price_band_normalized` uses the same `budget`/`midrange`/`premium`/`luxury`/`ultra_luxury` vocabulary as the spec.
- `photo_reference_value_overall` and the four coverage fields use the same `high`/`medium`/`low`/`unknown` vocabulary across schema, derive, and notes.
