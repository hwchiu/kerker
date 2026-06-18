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

    def test_render_venue_note_uses_quote_required_placeholder_for_missing_band(
        self,
    ) -> None:
        venue = venue_record()
        venue["pricing_status"] = "quote_required"
        derived = {
            "id": venue["id"],
            "name_zh": venue["name_zh"],
            "name_en_official": venue["name_en_official"],
            "region": venue["region"],
            "venue_types": venue["venue_types"],
            "pricing_status": venue["pricing_status"],
            "price_band_normalized": None,
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

        self.assertIn("- 價位帶：待詢價", note)
        self.assertNotIn("- 價位帶：None", note)

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

    def test_write_all_venue_notes_preserves_unmanaged_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_workspace_layout(root)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())
            readme = paths["notes"] / "README.md"
            readme.write_text("# Manual notes guide\n", encoding="utf-8")

            write_all_venue_notes(root)

            self.assertTrue(readme.exists())
            self.assertEqual(readme.read_text(encoding="utf-8"), "# Manual notes guide\n")

    def test_write_all_venue_notes_removes_stale_generated_notes_on_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ensure_workspace_layout(root)
            paths = workspace_paths(root)

            write_json_file(paths["sources"] / "example.json", source_record())
            write_json_file(paths["photos"] / "example.json", photo_records())
            write_json_file(paths["venues"] / "example.json", venue_record())
            readme = paths["notes"] / "README.md"
            readme.write_text("# Manual notes guide\n", encoding="utf-8")

            first_written = write_all_venue_notes(root)

            replacement_source = source_record()
            replacement_source["source_id"] = "garden-official"
            replacement_source["venue_id"] = "garden-venue"

            replacement_venue = venue_record()
            replacement_venue["id"] = "garden-venue"
            replacement_venue["name_zh"] = "花園宴會場"
            replacement_venue["name_en_official"] = "Garden Venue"
            replacement_venue["source_ids"] = ["garden-official"]
            replacement_venue["photo_index_id"] = "garden-venue"

            replacement_photos = photo_records()
            for index, photo in enumerate(replacement_photos, start=1):
                photo["photo_entry_id"] = f"garden-photo-{index}"
                photo["venue_id"] = "garden-venue"
                photo["source_id"] = "garden-official"

            write_json_file(paths["sources"] / "example.json", replacement_source)
            write_json_file(paths["photos"] / "example.json", replacement_photos)
            write_json_file(paths["venues"] / "example.json", replacement_venue)

            second_written = write_all_venue_notes(root)

            self.assertEqual(len(first_written), 1)
            self.assertEqual(len(second_written), 1)
            self.assertFalse((paths["notes"] / "example-cliffside-resort.md").exists())
            self.assertTrue((paths["notes"] / "garden-venue.md").exists())
            self.assertTrue(readme.exists())
            self.assertEqual(readme.read_text(encoding="utf-8"), "# Manual notes guide\n")


if __name__ == "__main__":
    unittest.main()
