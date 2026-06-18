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

    def test_summarize_photo_coverage_single_medium_signal_stays_medium_overall(self) -> None:
        entries = [
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-medium-1",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/medium-1",
                    "image_url_or_gallery_url": "https://example.com/images/medium-1.jpg",
                    "image_type": "official_wedding_gallery",
                    "scene_tags": ["cliffside-ceremony"],
                    "authenticity": "official_promotional",
                    "coverage_type": "single_image",
                    "decision_value": "medium",
                    "decision_notes": "Shows ceremony layout with usable detail",
                }
            ),
        ]

        coverage = summarize_photo_coverage(entries)

        self.assertEqual(coverage["photo_coverage_ceremony"], "medium")
        self.assertEqual(coverage["photo_reference_value_overall"], "medium")

    def test_summarize_photo_coverage_medium_signal_not_downgraded_by_low_signal(self) -> None:
        entries = [
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-medium-2",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/medium-2",
                    "image_url_or_gallery_url": "https://example.com/images/medium-2.jpg",
                    "image_type": "official_wedding_gallery",
                    "scene_tags": ["cliffside-ceremony"],
                    "authenticity": "official_promotional",
                    "coverage_type": "single_image",
                    "decision_value": "medium",
                    "decision_notes": "Usable ceremony photo",
                }
            ),
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-low-1",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/low-1",
                    "image_url_or_gallery_url": "https://example.com/images/low-1.jpg",
                    "image_type": "official_hotel_gallery",
                    "scene_tags": ["room"],
                    "authenticity": "official_promotional",
                    "coverage_type": "single_image",
                    "decision_value": "low",
                    "decision_notes": "Weak room overview",
                }
            ),
        ]

        coverage = summarize_photo_coverage(entries)

        self.assertEqual(coverage["photo_coverage_ceremony"], "medium")
        self.assertEqual(coverage["photo_coverage_accommodation"], "low")
        self.assertEqual(coverage["photo_reference_value_overall"], "medium")

    def test_summarize_photo_coverage_multiple_low_signals_only_reach_medium(self) -> None:
        entries = [
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-low-r1",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/low-r1",
                    "image_url_or_gallery_url": "https://example.com/images/low-r1.jpg",
                    "image_type": "official_wedding_gallery",
                    "scene_tags": ["guest-seating"],
                    "authenticity": "official_promotional",
                    "coverage_type": "single_image",
                    "decision_value": "low",
                    "decision_notes": "Weak reception angle one",
                }
            ),
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-low-r2",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/low-r2",
                    "image_url_or_gallery_url": "https://example.com/images/low-r2.jpg",
                    "image_type": "official_wedding_gallery",
                    "scene_tags": ["night-view"],
                    "authenticity": "official_promotional",
                    "coverage_type": "single_image",
                    "decision_value": "low",
                    "decision_notes": "Weak reception angle two",
                }
            ),
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-low-r3",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/low-r3",
                    "image_url_or_gallery_url": "https://example.com/images/low-r3.jpg",
                    "image_type": "official_wedding_gallery",
                    "scene_tags": ["floral-setup"],
                    "authenticity": "official_promotional",
                    "coverage_type": "single_image",
                    "decision_value": "low",
                    "decision_notes": "Weak reception angle three",
                }
            ),
            validate_photo_record(
                {
                    "photo_entry_id": "gallery-low-r4",
                    "venue_id": "ayana-resort-bali",
                    "source_id": "ayana-official-weddings",
                    "page_url": "https://example.com/gallery/low-r4",
                    "image_url_or_gallery_url": "https://example.com/images/low-r4.jpg",
                    "image_type": "official_wedding_gallery",
                    "scene_tags": ["garden-reception"],
                    "authenticity": "official_promotional",
                    "coverage_type": "single_image",
                    "decision_value": "low",
                    "decision_notes": "Weak reception angle four",
                }
            ),
        ]

        coverage = summarize_photo_coverage(entries)

        self.assertEqual(coverage["photo_coverage_reception"], "medium")


if __name__ == "__main__":
    unittest.main()
