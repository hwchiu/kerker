import unittest

from bali_wedding_research.schema import validate_source_record


class SourceSchemaTest(unittest.TestCase):
    def test_validate_source_record_accepts_valid_source(self) -> None:
        record = {
            "source_id": "ayana-official-weddings",
            "venue_id": "ayana-resort-bali",
            "source_type": "official",
            "source_name": "AYANA Weddings",
            "source_url": "https://example.com/ayana/weddings",
            "captured_at": "2026-06-18",
            "content_date_if_known": "2026-05-20",
            "language": "en",
            "evidence_categories": ["pricing", "photos", "restrictions"],
            "reliability_notes": "Official venue wedding page",
            "raw_excerpt_summary": "Contains package pricing, gallery links, and usage notes",
        }

        validated = validate_source_record(record)

        self.assertEqual(validated["source_type"], "official")
        self.assertEqual(
            validated["evidence_categories"],
            ["pricing", "photos", "restrictions"],
        )

    def test_validate_source_record_rejects_unknown_source_type(self) -> None:
        record = {
            "source_id": "bad-source",
            "venue_id": "ayana-resort-bali",
            "source_type": "travel-forum",
            "source_name": "Forum Post",
            "source_url": "https://example.com/forum",
            "captured_at": "2026-06-18",
            "content_date_if_known": None,
            "language": "en",
            "evidence_categories": ["pricing"],
            "reliability_notes": "Unknown source class",
            "raw_excerpt_summary": "Random comments",
        }

        with self.assertRaises(ValueError):
            validate_source_record(record)


if __name__ == "__main__":
    unittest.main()
