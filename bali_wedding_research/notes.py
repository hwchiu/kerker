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
        entry["id"]: entry for entry in build_derived_indexes(root)["venues"]
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
