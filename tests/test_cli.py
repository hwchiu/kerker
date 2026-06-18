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
