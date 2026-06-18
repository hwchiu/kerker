import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from bali_wedding_research.cli import main
from bali_wedding_research.io import write_json_file
from bali_wedding_research.paths import workspace_paths
from tests.sample_data import photo_records, source_record, venue_record


class CliTest(unittest.TestCase):
    def _run_main(
        self, argv: list[str]
    ) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = main(argv)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def _init_workspace(self, tmpdir: str) -> Path:
        exit_code, _, stderr = self._run_main(["init-workspace", "--root", tmpdir])
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        return Path(tmpdir)

    def test_init_workspace_creates_expected_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code, stdout, stderr = self._run_main(
                ["init-workspace", "--root", tmpdir]
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr, "")

            paths = workspace_paths(Path(tmpdir))
            self.assertTrue(paths["venues"].exists())
            self.assertTrue(paths["notes"].exists())
            self.assertEqual(
                stdout.splitlines(),
                [
                    str(paths["venues"]),
                    str(paths["photos"]),
                    str(paths["sources"]),
                    str(paths["seeds"]),
                    str(paths["derived"]),
                    str(paths["notes"]),
                ],
            )

    def test_validate_reports_record_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._init_workspace(tmpdir)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            exit_code, stdout, stderr = self._run_main(["validate", "--root", tmpdir])

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout, "validated venues=1 sources=1 photos=3\n")
            self.assertEqual(stderr, "")

    def test_build_derived_writes_output_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._init_workspace(tmpdir)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            exit_code, stdout, stderr = self._run_main(
                ["build-derived", "--root", tmpdir]
            )
            self.assertEqual(exit_code, 0)
            self.assertTrue((paths["derived"] / "venues-index.json").exists())
            self.assertTrue((paths["derived"] / "open-questions.json").exists())
            self.assertEqual(
                stdout.splitlines(),
                [
                    str(paths["derived"] / "venues-index.json"),
                    str(paths["derived"] / "open-questions.json"),
                ],
            )
            self.assertEqual(stderr, "")

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

    def test_missing_command_returns_exit_code_2(self) -> None:
        exit_code, stdout, stderr = self._run_main([])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("usage:", stderr)

    def test_invalid_command_returns_exit_code_2(self) -> None:
        exit_code, stdout, stderr = self._run_main(["bogus"])

        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("invalid choice", stderr)


if __name__ == "__main__":
    unittest.main()
