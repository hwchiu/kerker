import tempfile
import unittest
from pathlib import Path

from bali_wedding_research.io import write_json_file
from bali_wedding_research.notes import render_venue_note, write_all_venue_notes
from bali_wedding_research.paths import ensure_workspace_layout, workspace_paths
from tests.sample_data import photo_records, source_record, venue_record


class NotesTest(unittest.TestCase):
    def test_render_venue_note_contains_decision_sections(self) -> None:
        venue = venue_record()
        derived = {
            "id": venue["id"],
            "name_zh": venue["name_zh"],
            "name_en_official": venue["name_en_official"],
            "region": venue["region"],
            "venue_types": venue["venue_types"],
            "pricing_status": venue["pricing_status"],
            "price_band_normalized": "premium",
            "price_summary_text": venue["price_summary_text"],
            "rain_backup_status": venue["rain_backup_status"],
            "accommodation_fit": venue["accommodation_fit"],
            "restriction_level": venue["restriction_level"],
            "traffic_risk_level": venue["traffic_risk_level"],
            "best_for": venue["best_for"],
            "not_ideal_for": venue["not_ideal_for"],
            "key_strengths": venue["key_strengths"],
            "key_risks": venue["key_risks"],
            "open_questions": venue["open_questions"],
            "source_count": 1,
            "photo_count": 3,
            "photo_coverage_ceremony": "medium",
            "photo_coverage_reception": "medium",
            "photo_coverage_rain_backup": "unknown",
            "photo_coverage_accommodation": "low",
            "photo_reference_value_overall": "medium",
        }

        note = render_venue_note(venue, derived)

        self.assertIn("# 範例懸崖度假村 (Example Cliffside Resort)", note)
        self.assertIn("## 快速判讀", note)
        self.assertIn("## 適合誰", note)
        self.assertIn("## 主要風險", note)

    def test_write_all_venue_notes_creates_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_workspace_layout(root)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())

            written = write_all_venue_notes(root)

            self.assertEqual(len(written), 1)
            self.assertTrue(written[0].exists())


if __name__ == "__main__":
    unittest.main()
