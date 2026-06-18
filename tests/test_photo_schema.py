import unittest

from bali_wedding_research.schema import summarize_photo_coverage, validate_photo_record


class PhotoSchemaTest(unittest.TestCase):
    def test_validate_photo_record_accepts_real_wedding_gallery(self) -> None:
        record = {
            "photo_entry_id": "ayana-gallery-1",
            "venue_id": "ayana-resort-bali",
            "source_id": "ayana-official-weddings",
            "page_url": "https://example.com/ayana/gallery",
            "image_url_or_gallery_url": "https://example.com/images/ayana-1.jpg",
            "image_type": "real_wedding_feature",
            "scene_tags": ["cliffside-ceremony", "guest-seating"],
            "authenticity": "real_wedding",
            "coverage_type": "large_gallery",
            "decision_value": "high",
            "decision_notes": "Shows the ceremony aisle and guest seating scale",
        }

        validated = validate_photo_record(record)

        self.assertEqual(validated["authenticity"], "real_wedding")

    def test_validate_photo_record_rejects_unknown_scene_tag(self) -> None:
        record = {
            "photo_entry_id": "bad-scene",
            "venue_id": "ayana-resort-bali",
            "source_id": "ayana-official-weddings",
            "page_url": "https://example.com/ayana/gallery",
            "image_url_or_gallery_url": "https://example.com/images/ayana-2.jpg",
            "image_type": "official_wedding_gallery",
            "scene_tags": ["dragon-ceremony"],
            "authenticity": "official_promotional",
            "coverage_type": "small_gallery",
            "decision_value": "medium",
            "decision_notes": "Unsupported scene tag",
        }

        with self.assertRaises(ValueError):
            validate_photo_record(record)

    def test_summarize_photo_coverage_scores_relevant_scenes(self) -> None:
        entries = [
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-1",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/1",
                    "image_url_or_gallery_url": "https://example.com/images/1.jpg",
                    "image_type": "real_wedding_feature",
                    "scene_tags": ["cliffside-ceremony"],
                    "authenticity": "real_wedding",
                    "coverage_type": "large_gallery",
                    "decision_value": "high",
                    "decision_notes": "Clear ceremony aisle photo",
                }
            ),
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-2",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/2",
                    "image_url_or_gallery_url": "https://example.com/images/2.jpg",
                    "image_type": "real_wedding_feature",
                    "scene_tags": ["guest-seating", "night-view"],
                    "authenticity": "real_wedding",
                    "coverage_type": "large_gallery",
                    "decision_value": "high",
                    "decision_notes": "Shows reception seating and night ambiance",
                }
            ),
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-3",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/3",
                    "image_url_or_gallery_url": "https://example.com/images/3.jpg",
                    "image_type": "official_hotel_gallery",
                    "scene_tags": ["room"],
                    "authenticity": "official_promotional",
                    "coverage_type": "small_gallery",
                    "decision_value": "low",
                    "decision_notes": "Only one room overview",
                }
            ),
        ]

        coverage = summarize_photo_coverage(entries)

        self.assertEqual(coverage["photo_coverage_ceremony"], "medium")
        self.assertEqual(coverage["photo_coverage_reception"], "medium")
        self.assertEqual(coverage["photo_coverage_accommodation"], "low")
        self.assertEqual(coverage["photo_reference_value_overall"], "medium")


if __name__ == "__main__":
    unittest.main()
