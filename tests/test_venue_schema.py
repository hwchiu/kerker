import unittest

from bali_wedding_research.schema import validate_price_entry, validate_venue_record


class VenueSchemaTest(unittest.TestCase):
    def _base_price_entry(self) -> dict[str, object]:
        return {
            "label": "Cliffside chapel package",
            "currency": "USD",
            "amount_min": 8500,
            "amount_max": None,
            "pricing_year": 2026,
            "includes_stay": False,
            "includes_decoration": True,
            "includes_dinner": False,
            "includes_tax_service": False,
            "conditions_text": "Ceremony package only",
            "confidence": "high",
        }

    def _base_venue(self) -> dict[str, object]:
        return {
            "id": "ayana-resort-bali",
            "name_zh": "阿雅娜峇里島度假村",
            "name_en_official": "AYANA Resort Bali",
            "brand_or_group": "AYANA Hospitality",
            "venue_operator_type": "resort",
            "is_standalone": False,
            "region": "Jimbaran",
            "subarea": "Ayana Estate",
            "official_website": "https://example.com/ayana",
            "maps_url": "https://maps.example.com/ayana",
            "address_text": "Karang Mas Estate, Jimbaran, Bali",
            "venue_types": ["cliffside", "chapel"],
            "primary_visual_identity": "Cliffside chapel with ocean backdrop",
            "ceremony_space_types": ["chapel", "cliffside-terrace"],
            "reception_space_types": ["garden", "private-dining"],
            "supports_ceremony_only": True,
            "supports_ceremony_and_dinner": True,
            "supports_buyout": False,
            "supports_micro_wedding": True,
            "guest_capacity_ceremony_min": 10,
            "guest_capacity_ceremony_max": 80,
            "guest_capacity_dinner_min": 20,
            "guest_capacity_dinner_max": 120,
            "recommended_guest_size_band": "81-120",
            "pricing_status": "public_price_available",
            "price_entries": [self._base_price_entry()],
            "price_summary_text": "Public ceremony package starts at USD 8,500",
            "price_risk_level": "low",
            "rain_backup_status": "strong",
            "has_indoor_backup": True,
            "has_covered_backup": True,
            "backup_space_description": "Indoor function room held as weather backup",
            "backup_quality_notes": "Backup keeps sea-facing feel but moves indoors",
            "weather_exposure_notes": "Primary ceremony remains wind exposed",
            "airport_drive_time_minutes_estimate": 25,
            "transport_notes": "Straightforward airport access outside peak traffic",
            "traffic_risk_level": "medium",
            "onsite_accommodation_available": True,
            "onsite_room_inventory_notes": "Large integrated resort inventory",
            "nearby_accommodation_notes": "Additional Jimbaran hotels nearby",
            "accommodation_fit": "one_stop",
            "guest_mobility_notes": "Suitable for guests who prefer minimal transfers",
            "restriction_level": "medium",
            "noise_cutoff_notes": "Outdoor amplified music ends at 22:00",
            "external_vendor_policy": "Outside vendors allowed with coordination",
            "minimum_stay_requirement_notes": "No mandatory buyout for ceremony package",
            "minimum_spend_notes": "Dinner venue may require separate minimum spend",
            "drone_policy_notes": "Subject to weather and resort permission",
            "family_child_notes": "Family-friendly resort",
            "religious_or_space_use_notes": "Chapel is used for symbolic ceremonies",
            "operational_constraints_notes": "Sunset slots book early",
            "style_tags": ["ocean-view", "cliffside", "chapel"],
            "price_band_normalized": None,
            "best_for": ["Guests wanting a resort stay and iconic cliff views"],
            "not_ideal_for": ["Couples needing the lowest possible package price"],
            "key_strengths": ["Integrated stay experience", "Strong visual identity"],
            "key_risks": ["Sunset inventory pressure", "Outdoor wind exposure"],
            "data_completeness": "deep_complete",
            "research_status": "deep_research_complete",
            "last_verified_at": "2026-06-18",
            "data_freshness": "recent",
            "open_questions": [],
            "source_ids": ["ayana-official-weddings"],
            "photo_index_id": "ayana-resort-bali",
        }

    def test_validate_venue_record_normalizes_price_band_for_public_prices(self) -> None:
        validated = validate_venue_record(self._base_venue())

        self.assertEqual(validated["price_band_normalized"], "premium")
        self.assertEqual(validated["price_risk_level"], "low")

    def test_validate_venue_record_requires_high_risk_for_quote_only(self) -> None:
        record = self._base_venue()
        record["pricing_status"] = "quote_required"
        record["price_entries"] = []
        record["price_summary_text"] = "Quote required"
        record["price_risk_level"] = "low"
        record["price_band_normalized"] = None

        with self.assertRaises(ValueError):
            validate_venue_record(record)

    def test_validate_price_entry_rejects_bool_amount_min(self) -> None:
        entry = self._base_price_entry()
        entry["amount_min"] = True

        with self.assertRaises(ValueError):
            validate_price_entry(entry)

    def test_validate_price_entry_rejects_bool_pricing_year(self) -> None:
        entry = self._base_price_entry()
        entry["pricing_year"] = True

        with self.assertRaises(ValueError):
            validate_price_entry(entry)

    def test_validate_price_entry_rejects_nan_amount_min(self) -> None:
        entry = self._base_price_entry()
        entry["amount_min"] = float("nan")

        with self.assertRaises(ValueError):
            validate_price_entry(entry)

    def test_validate_price_entry_rejects_infinite_amount_min(self) -> None:
        entry = self._base_price_entry()
        entry["amount_min"] = float("inf")

        with self.assertRaises(ValueError):
            validate_price_entry(entry)

    def test_validate_price_entry_rejects_negative_amount_min(self) -> None:
        entry = self._base_price_entry()
        entry["amount_min"] = -1

        with self.assertRaises(ValueError):
            validate_price_entry(entry)

    def test_validate_price_entry_rejects_amount_min_greater_than_amount_max(self) -> None:
        entry = self._base_price_entry()
        entry["amount_min"] = 9000
        entry["amount_max"] = 8500

        with self.assertRaises(ValueError):
            validate_price_entry(entry)

    def test_validate_venue_record_normalizes_lowercase_usd_currency(self) -> None:
        record = self._base_venue()
        record["price_entries"] = [self._base_price_entry()]
        record["price_entries"][0]["currency"] = "usd"

        validated = validate_venue_record(record)

        self.assertEqual(validated["price_entries"][0]["currency"], "USD")
        self.assertEqual(validated["price_band_normalized"], "premium")
        self.assertEqual(validated["price_risk_level"], "low")

    def test_validate_venue_record_rejects_low_risk_when_public_price_has_no_usd_minimum(self) -> None:
        record = self._base_venue()
        record["price_entries"] = [self._base_price_entry()]
        record["price_entries"][0]["currency"] = "EUR"
        record["price_risk_level"] = "low"
        record["price_band_normalized"] = None

        with self.assertRaises(ValueError):
            validate_venue_record(record)

    def test_validate_venue_record_accepts_high_risk_when_public_price_has_no_usd_minimum(self) -> None:
        record = self._base_venue()
        record["price_entries"] = [self._base_price_entry()]
        record["price_entries"][0]["currency"] = "EUR"
        record["price_risk_level"] = "high"
        record["price_band_normalized"] = None

        validated = validate_venue_record(record)

        self.assertIsNone(validated["price_band_normalized"])
        self.assertEqual(validated["price_risk_level"], "high")

    def test_validate_venue_record_rejects_unknown_status_with_public_price_entries(self) -> None:
        record = self._base_venue()
        record["pricing_status"] = "unknown"
        record["price_risk_level"] = "high"
        record["price_band_normalized"] = None

        with self.assertRaisesRegex(
            ValueError,
            "pricing_status=unknown must not carry public price entries",
        ):
            validate_venue_record(record)

    def test_validate_venue_record_rejects_public_price_available_without_price_entries(self) -> None:
        record = self._base_venue()
        record["price_entries"] = []
        record["pricing_status"] = "public_price_available"
        record["price_risk_level"] = "high"
        record["price_band_normalized"] = None

        with self.assertRaisesRegex(
            ValueError,
            "pricing_status=public_price_available requires at least one public price entry",
        ):
            validate_venue_record(record)


if __name__ == "__main__":
    unittest.main()
