import unittest
import tempfile
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
