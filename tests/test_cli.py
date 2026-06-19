import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from bali_wedding_research.cli import main
from bali_wedding_research.io import load_json_file, write_json_file
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
                    str(paths["photo_assets"]),
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
            root = self._init_workspace(tmpdir)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            exit_code, stdout, stderr = self._run_main(["build-notes", "--root", tmpdir])
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                stdout.splitlines(),
                [str(paths["notes"] / "example-cliffside-resort.md")],
            )
            self.assertEqual(stderr, "")
            self.assertTrue((paths["notes"] / "example-cliffside-resort.md").exists())

    def test_build_site_writes_static_site_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._init_workspace(tmpdir)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            exit_code, stdout, stderr = self._run_main(["build-site", "--root", tmpdir])

            site_root = root / "site"
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                stdout.splitlines(),
                [
                    str(site_root / "index.html"),
                    str(site_root / "assets" / "site.css"),
                    str(site_root / "assets" / "site.js"),
                    str(site_root / "venues" / "example-cliffside-resort.html"),
                ],
            )
            self.assertEqual(stderr, "")
            self.assertTrue((site_root / "index.html").exists())
            self.assertTrue((site_root / "venues" / "example-cliffside-resort.html").exists())

    def test_build_pages_site_writes_docs_site_and_redirect_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._init_workspace(tmpdir)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            exit_code, stdout, stderr = self._run_main(
                ["build-pages-site", "--root", tmpdir]
            )

            docs_root = root / "docs"
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                stdout.splitlines(),
                [
                    str(docs_root / "index.html"),
                    str(docs_root / "assets" / "site.css"),
                    str(docs_root / "assets" / "site.js"),
                    str(docs_root / "venues" / "example-cliffside-resort.html"),
                    str(docs_root / ".nojekyll"),
                    str(root / "index.html"),
                    str(root / ".nojekyll"),
                ],
            )
            self.assertEqual(stderr, "")
            self.assertTrue((docs_root / "index.html").exists())
            self.assertTrue((docs_root / ".nojekyll").exists())
            self.assertTrue((root / "index.html").exists())
            self.assertTrue((root / ".nojekyll").exists())

    def test_build_photo_assets_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._init_workspace(tmpdir)
            paths = workspace_paths(root)
            manifest_path = paths["derived"] / "photo-assets.json"

            with patch("bali_wedding_research.cli.write_photo_assets") as write_photo_assets_mock:
                write_photo_assets_mock.return_value = manifest_path
                exit_code, stdout, stderr = self._run_main(
                    [
                        "build-photo-assets",
                        "--root",
                        tmpdir,
                        "--max-images-per-photo",
                        "4",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout, f"{manifest_path}\n")
            self.assertEqual(stderr, "")
            write_photo_assets_mock.assert_called_once_with(root, max_images_per_photo=4)

    def test_serve_site_invokes_server_with_expected_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self._init_workspace(tmpdir)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            with patch("bali_wedding_research.cli.serve_site") as serve_site_mock:
                exit_code, stdout, stderr = self._run_main(
                    [
                        "serve-site",
                        "--root",
                        tmpdir,
                        "--host",
                        "0.0.0.0",
                        "--port",
                        "8123",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout, "")
            self.assertEqual(stderr, "")
            serve_site_mock.assert_called_once_with(
                root,
                root / "site",
                host="0.0.0.0",
                port=8123,
            )

    def test_merge_seeds_writes_canonical_seed_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            exit_code, _, stderr = self._run_main(["init-workspace", "--root", tmpdir])
            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr, "")
            paths = workspace_paths(root)

            raw_a = root / "seed-a.json"
            raw_b = root / "seed-b.json"

            write_json_file(
                raw_a,
                [
                    {
                        "seed_id": "example-cliffside-resort",
                        "name_en": "Example Cliffside Resort",
                        "aliases": ["Example Cliffside"],
                        "region": "Uluwatu",
                        "discovery_urls": ["https://example.com/seed-a"],
                        "status": "candidate",
                    }
                ],
            )
            write_json_file(
                raw_b,
                [
                    {
                        "seed_id": "example-cliffside-listing",
                        "name_en": "Example Cliffside",
                        "aliases": ["Example Cliffside Resort"],
                        "region": "Uluwatu",
                        "discovery_urls": ["https://example.com/seed-b"],
                        "status": "candidate",
                    }
                ],
            )

            exit_code, stdout, stderr = self._run_main(
                [
                    "merge-seeds",
                    "--root",
                    tmpdir,
                    "--input",
                    str(raw_a),
                    "--input",
                    str(raw_b),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr, "")
            merged_path = paths["seeds"] / "venue-seeds.json"
            self.assertEqual(stdout, f"{merged_path}\n")
            self.assertTrue(merged_path.exists())
            merged = load_json_file(merged_path)
            self.assertEqual(len(merged), 1)
            self.assertEqual(
                merged[0]["discovery_urls"],
                ["https://example.com/seed-a", "https://example.com/seed-b"],
            )

    def test_merge_seeds_writes_disconnected_groups_in_stable_order(self) -> None:
        seed_alpha = {
            "seed_id": "alpha-beach-club",
            "name_en": "Alpha Beach Club",
            "aliases": [],
            "region": "Seminyak",
            "discovery_urls": ["https://example.com/alpha"],
            "status": "candidate",
        }
        seed_zeta = {
            "seed_id": "zeta-garden-villa",
            "name_en": "Zeta Garden Villa",
            "aliases": [],
            "region": "Ubud",
            "discovery_urls": ["https://example.com/zeta"],
            "status": "candidate",
        }

        with tempfile.TemporaryDirectory() as tmpdir_a, tempfile.TemporaryDirectory() as tmpdir_b:
            root_a = self._init_workspace(tmpdir_a)
            paths_a = workspace_paths(root_a)
            alpha_path_a = root_a / "alpha.json"
            zeta_path_a = root_a / "zeta.json"
            write_json_file(alpha_path_a, [seed_alpha])
            write_json_file(zeta_path_a, [seed_zeta])

            exit_code, stdout, stderr = self._run_main(
                [
                    "merge-seeds",
                    "--root",
                    tmpdir_a,
                    "--input",
                    str(zeta_path_a),
                    "--input",
                    str(alpha_path_a),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr, "")
            merged_path_a = paths_a["seeds"] / "venue-seeds.json"
            self.assertEqual(stdout, f"{merged_path_a}\n")
            merged_a = load_json_file(merged_path_a)

            root_b = self._init_workspace(tmpdir_b)
            paths_b = workspace_paths(root_b)
            alpha_path_b = root_b / "alpha.json"
            zeta_path_b = root_b / "zeta.json"
            write_json_file(alpha_path_b, [seed_alpha])
            write_json_file(zeta_path_b, [seed_zeta])

            exit_code, stdout, stderr = self._run_main(
                [
                    "merge-seeds",
                    "--root",
                    tmpdir_b,
                    "--input",
                    str(alpha_path_b),
                    "--input",
                    str(zeta_path_b),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr, "")
            merged_path_b = paths_b["seeds"] / "venue-seeds.json"
            self.assertEqual(stdout, f"{merged_path_b}\n")
            merged_b = load_json_file(merged_path_b)

            self.assertEqual(
                [entry["seed_id"] for entry in merged_a],
                ["alpha-beach-club", "zeta-garden-villa"],
            )
            self.assertEqual(merged_a, merged_b)

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
