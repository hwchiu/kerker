import unittest

from bali_wedding_research.schema import validate_source_record


def make_source_record(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
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
    record.update(overrides)
    return record


class SourceSchemaTest(unittest.TestCase):
    def test_validate_source_record_accepts_valid_source(self) -> None:
        validated = validate_source_record(make_source_record())

        self.assertEqual(validated["source_type"], "official")
        self.assertEqual(
            validated["evidence_categories"],
            ["pricing", "photos", "restrictions"],
        )

    def test_validate_source_record_rejects_unknown_source_type(self) -> None:
        with self.assertRaises(ValueError):
            validate_source_record(
                make_source_record(
                    source_id="bad-source",
                    source_type="travel-forum",
                    source_name="Forum Post",
                    source_url="https://example.com/forum",
                    content_date_if_known=None,
                    evidence_categories=["pricing"],
                    reliability_notes="Unknown source class",
                    raw_excerpt_summary="Random comments",
                )
            )

    def test_validate_source_record_accepts_none_content_date_if_known(self) -> None:
        validated = validate_source_record(make_source_record(content_date_if_known=None))

        self.assertIsNone(validated["content_date_if_known"])

    def test_validate_source_record_rejects_unsupported_evidence_categories(self) -> None:
        with self.assertRaisesRegex(ValueError, "evidence_categories"):
            validate_source_record(
                make_source_record(evidence_categories=["pricing", "unknown-category"])
            )

    def test_validate_source_record_rejects_invalid_iso_dates_with_field_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "captured_at"):
            validate_source_record(make_source_record(captured_at="2026/06/18"))

    def test_validate_source_record_returns_normalized_values(self) -> None:
        validated = validate_source_record(
            make_source_record(
                source_id=" ayana-official-weddings ",
                venue_id=" ayana-resort-bali ",
                source_name=" AYANA Weddings ",
                source_url=" https://example.com/ayana/weddings ",
                captured_at="20260618",
                content_date_if_known="20260520",
                language=" en ",
                evidence_categories=[" pricing ", " photos ", " restrictions "],
                reliability_notes=" Official venue wedding page ",
                raw_excerpt_summary=" Contains package pricing, gallery links, and usage notes ",
            )
        )

        self.assertEqual(validated["source_id"], "ayana-official-weddings")
        self.assertEqual(validated["venue_id"], "ayana-resort-bali")
        self.assertEqual(validated["source_name"], "AYANA Weddings")
        self.assertEqual(validated["source_url"], "https://example.com/ayana/weddings")
        self.assertEqual(validated["captured_at"], "2026-06-18")
        self.assertEqual(validated["content_date_if_known"], "2026-05-20")
        self.assertEqual(validated["language"], "en")
        self.assertEqual(
            validated["evidence_categories"],
            ["pricing", "photos", "restrictions"],
        )
        self.assertEqual(validated["reliability_notes"], "Official venue wedding page")
        self.assertEqual(
            validated["raw_excerpt_summary"],
            "Contains package pricing, gallery links, and usage notes",
        )


if __name__ == "__main__":
    unittest.main()
