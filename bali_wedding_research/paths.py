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
