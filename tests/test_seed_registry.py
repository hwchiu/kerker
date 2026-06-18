import unittest

from bali_wedding_research.seed_registry import merge_seed_registry, slugify_name


def make_seed_entry(**overrides: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "seed_id": "seed-id",
        "name_en": "Venue Name",
        "aliases": [],
        "region": "Jimbaran",
        "discovery_urls": ["https://example.com/default"],
        "status": "candidate",
    }
    entry.update(overrides)
    return entry


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

    def test_merge_seed_registry_collapses_bridged_alias_groups(self) -> None:
        entries = [
            {
                "seed_id": "alpha-venue",
                "name_en": "Alpha Venue",
                "aliases": ["Alpha Bali"],
                "region": "Jimbaran",
                "discovery_urls": ["https://example.com/alpha-official"],
                "status": "candidate",
            },
            {
                "seed_id": "bravo-venue",
                "name_en": "Bravo Venue",
                "aliases": ["Bravo Bali"],
                "region": "Jimbaran",
                "discovery_urls": ["https://example.com/bravo-official"],
                "status": "candidate",
            },
            {
                "seed_id": "alpha-bravo-listing",
                "name_en": "Alpha Bali",
                "aliases": ["Bravo Venue"],
                "region": "Jimbaran",
                "discovery_urls": ["https://example.com/alpha-bravo-listing"],
                "status": "candidate",
            },
        ]

        merged = merge_seed_registry(entries)

        self.assertEqual(len(merged), 1)
        self.assertEqual(
            merged[0]["discovery_urls"],
            [
                "https://example.com/alpha-bravo-listing",
                "https://example.com/alpha-official",
                "https://example.com/bravo-official",
            ],
        )
        self.assertEqual(
            merged[0]["aliases"],
            ["Alpha Bali", "Alpha Venue", "Bravo Bali", "Bravo Venue"],
        )

    def test_merge_seed_registry_is_deterministic_for_connected_entries(self) -> None:
        entries = [
            make_seed_entry(
                seed_id="zeta-venue",
                name_en="Zeta Venue",
                aliases=["Zeta Bali"],
                discovery_urls=["https://example.com/zeta-official"],
            ),
            make_seed_entry(
                seed_id="beta-venue",
                name_en="Beta Venue",
                aliases=["Beta Bali"],
                discovery_urls=["https://example.com/beta-official"],
            ),
            make_seed_entry(
                seed_id="zeta-beta-listing",
                name_en="Beta Bali",
                aliases=["Zeta Venue"],
                discovery_urls=["https://example.com/zeta-beta-listing"],
            ),
        ]
        expected = [
            {
                "seed_id": "beta-venue",
                "name_en": "Beta Venue",
                "aliases": ["Beta Bali", "Beta Venue", "Zeta Bali", "Zeta Venue"],
                "region": "Jimbaran",
                "discovery_urls": [
                    "https://example.com/beta-official",
                    "https://example.com/zeta-beta-listing",
                    "https://example.com/zeta-official",
                ],
                "status": "candidate",
            }
        ]

        self.assertEqual(merge_seed_registry(entries), expected)
        self.assertEqual(merge_seed_registry(list(reversed(entries))), expected)

    def test_merge_seed_registry_prefers_record_created_over_earlier_candidate(self) -> None:
        entries = [
            make_seed_entry(
                seed_id="alpha-candidate",
                name_en="Alpha Venue",
                aliases=["Alpha Bali"],
                discovery_urls=["https://example.com/alpha-candidate"],
                status="candidate",
            ),
            make_seed_entry(
                seed_id="zeta-record",
                name_en="Alpha Venue Official",
                aliases=["Alpha Venue"],
                discovery_urls=["https://example.com/alpha-record"],
                status="record_created",
            ),
        ]

        self.assertEqual(
            merge_seed_registry(entries),
            [
                {
                    "seed_id": "zeta-record",
                    "name_en": "Alpha Venue Official",
                    "aliases": [
                        "Alpha Bali",
                        "Alpha Venue",
                        "Alpha Venue Official",
                    ],
                    "region": "Jimbaran",
                    "discovery_urls": [
                        "https://example.com/alpha-candidate",
                        "https://example.com/alpha-record",
                    ],
                    "status": "record_created",
                }
            ],
        )

    def test_merge_seed_registry_prefers_rejected_over_earlier_candidate(self) -> None:
        entries = [
            make_seed_entry(
                seed_id="alpha-candidate",
                name_en="Citra Venue",
                aliases=["Citra Bali"],
                discovery_urls=["https://example.com/citra-candidate"],
                status="candidate",
            ),
            make_seed_entry(
                seed_id="zeta-rejected",
                name_en="Citra Venue Rejected",
                aliases=["Citra Venue"],
                discovery_urls=["https://example.com/citra-rejected"],
                status="rejected",
            ),
        ]

        self.assertEqual(
            merge_seed_registry(entries),
            [
                {
                    "seed_id": "zeta-rejected",
                    "name_en": "Citra Venue Rejected",
                    "aliases": [
                        "Citra Bali",
                        "Citra Venue",
                        "Citra Venue Rejected",
                    ],
                    "region": "Jimbaran",
                    "discovery_urls": [
                        "https://example.com/citra-candidate",
                        "https://example.com/citra-rejected",
                    ],
                    "status": "rejected",
                }
            ],
        )

    def test_merge_seed_registry_rejects_conflicting_regions_within_alias_group(self) -> None:
        entries = [
            make_seed_entry(
                seed_id="alpha-jimbaran",
                name_en="Delta Venue",
                aliases=["Delta Bali"],
                region="Jimbaran",
                discovery_urls=["https://example.com/delta-jimbaran"],
            ),
            make_seed_entry(
                seed_id="delta-ubud",
                name_en="Delta Bali",
                aliases=["Delta Venue"],
                region="Ubud",
                discovery_urls=["https://example.com/delta-ubud"],
            ),
        ]

        with self.assertRaisesRegex(ValueError, "region"):
            merge_seed_registry(entries)


if __name__ == "__main__":
    unittest.main()
