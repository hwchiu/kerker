import tempfile
import unittest
from pathlib import Path

from bali_wedding_research.paths import ensure_workspace_layout, workspace_paths


class WorkspacePathsTest(unittest.TestCase):
    def test_workspace_paths_points_to_expected_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            paths = workspace_paths(root)

            self.assertEqual(paths["root"], root.resolve())
            self.assertEqual(paths["venues"], root / "data" / "venues")
            self.assertEqual(paths["photos"], root / "data" / "photos")
            self.assertEqual(paths["sources"], root / "data" / "sources")
            self.assertEqual(paths["seeds"], root / "data" / "seeds")
            self.assertEqual(paths["derived"], root / "data" / "derived")
            self.assertEqual(paths["notes"], root / "content" / "venue-notes")

    def test_ensure_workspace_layout_creates_all_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            created = ensure_workspace_layout(root)

            self.assertEqual(
                created,
                [
                    root / "data" / "venues",
                    root / "data" / "photos",
                    root / "data" / "sources",
                    root / "data" / "seeds",
                    root / "data" / "derived",
                    root / "content" / "venue-notes",
                ],
            )
            self.assertTrue(all(path.exists() for path in created))


if __name__ == "__main__":
    unittest.main()
