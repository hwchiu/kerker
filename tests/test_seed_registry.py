import unittest

from bali_wedding_research.seed_registry import merge_seed_registry, slugify_name


class SeedRegistryTest(unittest.TestCase):
    def test_slugify_name_normalizes_spacing_and_case(self) -> None:
        self.assertEqual(slugify_name("AYANA Resort Bali"), "ayana-resort-bali")
        self.assertEqual(slugify_name("The Edge Uluwatu"), "the-edge-uluwatu")

    def test_merge_seed_registry_merges_alias_matches(self) -> None:
        entries = [
            {
                "seed_id": "ayana-resort-bali",
                "name_en": "AYANA Resort Bali",
                "aliases": ["AYANA Bali"],
                "region": "Jimbaran",
                "discovery_urls": ["https://example.com/ayana-official"],
                "status": "candidate",
            },
            {
                "seed_id": "ayana-bali-listing",
                "name_en": "AYANA Bali",
                "aliases": ["AYANA Resort Bali"],
                "region": "Jimbaran",
                "discovery_urls": ["https://example.com/ayana-listing"],
                "status": "candidate",
            },
        ]

        merged = merge_seed_registry(entries)

        self.assertEqual(len(merged), 1)
        self.assertEqual(
            merged[0]["discovery_urls"],
            ["https://example.com/ayana-listing", "https://example.com/ayana-official"],
        )
        self.assertEqual(
            merged[0]["aliases"],
            ["AYANA Bali", "AYANA Resort Bali"],
        )


if __name__ == "__main__":
    unittest.main()
