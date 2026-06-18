import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from bali_wedding_research.derive import build_derived_indexes, write_derived_indexes
from bali_wedding_research.io import load_json_file, validate_workspace, write_json_file
from bali_wedding_research.paths import ensure_workspace_layout, workspace_paths
from tests.sample_data import photo_records, source_record, venue_record


class DerivedIndexTest(unittest.TestCase):
    def write_workspace(
        self,
        root: Path,
        *,
        venues: list[dict[str, object]] | None = None,
        sources: list[dict[str, object]] | None = None,
        photos: list[dict[str, object]] | None = None,
    ) -> dict[str, Path]:
        ensure_workspace_layout(root)
        paths = workspace_paths(root)
        write_json_file(paths["venues"] / "records.json", venues or [venue_record()])
        write_json_file(paths["sources"] / "records.json", sources or [source_record()])
        write_json_file(paths["photos"] / "records.json", photos or photo_records())
        return paths

    def make_venue(
        self,
        *,
        venue_id: str = "example-cliffside-resort",
        source_ids: list[str] | None = None,
    ) -> dict[str, object]:
        venue = deepcopy(venue_record())
        venue["id"] = venue_id
        venue["photo_index_id"] = venue_id
        if source_ids is not None:
            venue["source_ids"] = source_ids
        return venue

    def make_source(
        self,
        *,
        source_id: str = "example-cliffside-official",
        venue_id: str = "example-cliffside-resort",
    ) -> dict[str, object]:
        source = deepcopy(source_record())
        source["source_id"] = source_id
        source["venue_id"] = venue_id
        return source

    def make_photos(self) -> list[dict[str, object]]:
        return deepcopy(photo_records())

    def test_validate_workspace_and_write_derived_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = self.write_workspace(root)

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

    def test_validate_workspace_rejects_duplicate_venue_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            venues = [self.make_venue(), self.make_venue()]

            self.write_workspace(root, venues=venues)

            with self.assertRaisesRegex(ValueError, "duplicate venue id: example-cliffside-resort"):
                validate_workspace(root)

    def test_validate_workspace_rejects_duplicate_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = [self.make_source(), self.make_source()]

            self.write_workspace(root, sources=sources)

            with self.assertRaisesRegex(ValueError, "duplicate source_id: example-cliffside-official"):
                validate_workspace(root)

    def test_validate_workspace_rejects_duplicate_photo_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            photos = self.make_photos()
            photos[1]["photo_entry_id"] = photos[0]["photo_entry_id"]

            self.write_workspace(root, photos=photos)

            with self.assertRaisesRegex(ValueError, "duplicate photo_entry_id: example-photo-1"):
                validate_workspace(root)

    def test_validate_workspace_rejects_source_with_missing_venue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = [self.make_source(venue_id="missing-venue")]

            self.write_workspace(root, sources=sources)

            with self.assertRaisesRegex(
                ValueError,
                "source example-cliffside-official references missing venue: missing-venue",
            ):
                validate_workspace(root)

    def test_validate_workspace_rejects_photo_source_venue_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            venues = [
                self.make_venue(),
                self.make_venue(
                    venue_id="example-garden-resort",
                    source_ids=["example-garden-official"],
                ),
            ]
            sources = [
                self.make_source(),
                self.make_source(
                    source_id="example-garden-official",
                    venue_id="example-garden-resort",
                ),
            ]
            photos = self.make_photos()
            photos[0]["source_id"] = "example-garden-official"

            self.write_workspace(root, venues=venues, sources=sources, photos=photos)

            with self.assertRaisesRegex(
                ValueError,
                "photo example-photo-1 source example-garden-official belongs to venue "
                "example-garden-resort, not example-cliffside-resort",
            ):
                validate_workspace(root)

    def test_validate_workspace_rejects_venue_with_missing_source_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            venues = [self.make_venue(source_ids=["missing-source-id"])]

            self.write_workspace(root, venues=venues)

            with self.assertRaisesRegex(
                ValueError,
                "venue example-cliffside-resort references missing sources: missing-source-id",
            ):
                validate_workspace(root)


if __name__ == "__main__":
    unittest.main()
