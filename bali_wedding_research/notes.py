from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .derive import build_derived_indexes
from .io import load_workspace_records
from .paths import ensure_workspace_layout, workspace_paths


def _generated_notes_manifest_path(notes_dir: Path) -> Path:
    return notes_dir / ".generated-notes.json"


def _load_generated_note_names(notes_dir: Path) -> set[str]:
    manifest_path = _generated_notes_manifest_path(notes_dir)
    if not manifest_path.exists():
        return set()

    with manifest_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, list):
        return set()

    return {
        item
        for item in payload
        if isinstance(item, str) and item.endswith(".md") and Path(item).name == item
    }


def _write_generated_note_names(notes_dir: Path, note_names: set[str]) -> None:
    manifest_path = _generated_notes_manifest_path(notes_dir)
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(sorted(note_names), handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _display_price_band(derived_entry: dict[str, Any]) -> str:
    price_band = derived_entry.get("price_band_normalized")
    if price_band:
        return str(price_band)
    if derived_entry.get("pricing_status") == "quote_required":
        return "待詢價"
    return "未知"


def render_venue_note(venue: dict[str, Any], derived_entry: dict[str, Any]) -> str:
    venue_types = ", ".join(venue["venue_types"])
    quick_scan_rows = [
        ("地區", venue["region"]),
        ("場地型態", venue_types),
        ("價格狀態", venue["pricing_status"]),
        ("價位帶", _display_price_band(derived_entry)),
        ("雨備強度", venue["rain_backup_status"]),
        ("住宿整合", venue["accommodation_fit"]),
        ("交通風險", venue["traffic_risk_level"]),
        ("照片參考價值", derived_entry["photo_reference_value_overall"]),
    ]
    quick_scan_table = "\n".join(
        [
            "| 項目 | 內容 |",
            "| --- | --- |",
            *[f"| {label} | {value} |" for label, value in quick_scan_rows],
        ]
    )
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
        f"{quick_scan_table}\n\n"
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
        entry["id"]: entry for entry in build_derived_indexes(root)["venues"]
    }
    previous_note_names = _load_generated_note_names(paths["notes"])
    current_note_names = {f"{venue['id']}.md" for venue in venues}

    for note_name in previous_note_names - current_note_names:
        existing_note = paths["notes"] / note_name
        if existing_note.exists():
            existing_note.unlink()

    written: list[Path] = []
    for venue in venues:
        target = paths["notes"] / f"{venue['id']}.md"
        target.write_text(
            render_venue_note(venue, derived_lookup[venue["id"]]),
            encoding="utf-8",
        )
        written.append(target)

    _write_generated_note_names(paths["notes"], current_note_names)
    return written
