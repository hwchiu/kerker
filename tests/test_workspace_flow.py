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
