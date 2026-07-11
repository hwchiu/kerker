from __future__ import annotations

from pathlib import Path


def _destination_data_root(resolved_root: Path, destination_id: str | None) -> Path:
    if destination_id in (None, "bali"):
        return resolved_root / "data"
    return resolved_root / "data" / "destinations" / destination_id


def workspace_paths(root: Path, destination_id: str | None = None) -> dict[str, Path]:
    resolved_root = root.resolve()
    path_root = root if root.is_absolute() else resolved_root
    data_root = _destination_data_root(path_root, destination_id)
    notes_root = (
        path_root / "content" / "venue-notes"
        if destination_id in (None, "bali")
        else path_root / "content" / "venue-notes" / destination_id
    )
    return {
        "root": resolved_root,
        "data": data_root,
        "venues": data_root / "venues",
        "photos": data_root / "photos",
        "sources": data_root / "sources",
        "seeds": data_root / "seeds",
        "derived": data_root / "derived",
        "photo_assets": data_root / "photo-assets",
        "notes": notes_root,
    }


def ensure_workspace_layout(root: Path, destination_id: str | None = None) -> list[Path]:
    paths = workspace_paths(root, destination_id)
    created: list[Path] = []
    for key in ("venues", "photos", "sources", "seeds", "derived", "photo_assets", "notes"):
        directory = paths[key]
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)
    return created
