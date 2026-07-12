import hashlib
import json
import unittest
from pathlib import Path

from bali_wedding_research.photo_assets import (
    EXCLUDED_SITE_ASSET_FILENAMES,
    _is_venue_photo,
)


ROOT = Path(__file__).resolve().parents[1]


def _load_json_records(directory: Path) -> list[dict]:
    records: list[dict] = []
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        records.extend(payload if isinstance(payload, list) else [payload])
    return records


class DataQualityTest(unittest.TestCase):
    def test_conrad_bali_does_not_use_generic_balifortwo_real_wedding_pages(self) -> None:
        offenders = []
        for source in _load_json_records(ROOT / "data" / "sources"):
            source_id = source["source_id"]
            source_url = source["source_url"]
            if source["venue_id"] != "conrad-bali":
                continue
            if not source_id.startswith("conrad-bali-balifortwo-"):
                continue
            if "/real-weddings/" in source_url and "conrad" not in source_url.lower():
                offenders.append(source_id)

        self.assertEqual(offenders, [])

    def test_bali_site_photos_are_not_reused_across_venues(self) -> None:
        by_hash: dict[str, list[Path]] = {}
        photos_root = ROOT / "docs" / "bali" / "assets" / "photos"
        for path in sorted(photos_root.glob("*/*")):
            if path.name in EXCLUDED_SITE_ASSET_FILENAMES:
                continue
            if path.suffix.lower() == ".gif":
                continue
            content = path.read_bytes()
            if not _is_venue_photo(content):
                continue
            digest = hashlib.md5(content).hexdigest()
            by_hash.setdefault(digest, []).append(path)

        offenders = []
        for paths in by_hash.values():
            venues = {path.parent.name for path in paths}
            if len(venues) > 1:
                offenders.append([path.relative_to(ROOT).as_posix() for path in paths])

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
