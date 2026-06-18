# Bali Wedding Venue Research Database Design

## Context

The user wants a deep, decision-ready research system for Bali wedding venues with enough structure to support a later local search website. The immediate priority is not the website itself. The immediate priority is collecting, normalizing, and indexing venue information so the user can quickly eliminate unsuitable options and compare strong candidates.

This work is intentionally split into two subprojects:

1. Phase 1: Bali wedding venue research database
2. Phase 2: Local search website powered by the Phase 1 data

This document defines Phase 1 and the data contracts that Phase 2 will consume.

## User Goals

- Build as complete a Bali venue list as practical, centered on hotels and resorts, while also including representative standalone venues.
- Collect public pricing when available and retain venues that require quotation.
- Prioritize deep research over shallow list-building.
- Support fast elimination based on style, guest count, pricing, rain backup, transport, and accommodation fit.
- Preserve official English venue names while presenting the research primarily in Traditional Chinese.
- Include as many useful wedding-related photos as practical, especially photos that help compare ceremony, dinner, backup, and guest experience.
- Exclude wedding planners, photographers, hair/makeup, and legal paperwork from Phase 1.

## Scope

### In Scope

- Wedding-capable Bali hotels, resorts, and representative standalone venues
- Venue, hotel, and wedding-package research
- Price capture and normalization
- Capacity, usage model, and restrictions capture
- Rain backup research
- Transport and accommodation suitability research
- Photo source indexing and photo usefulness classification
- Structured source tracking
- Derived search-friendly dataset for a future local website

### Out of Scope

- Wedding planner/vendor ecosystem research
- Photography, videography, makeup, styling, entertainment, florals, or production sourcing
- Legal marriage procedures
- Booking automation or inquiry automation
- The user-facing website implementation itself
- Downloading and rehosting third-party images in Phase 1

## Success Criteria

Phase 1 is successful when:

- The repository contains a maintainable research system rather than a single flat note.
- Each researched venue has a canonical record with core decision fields.
- Each important claim can be traced to one or more sources.
- Price information is preserved even when incomplete or conflicting.
- Photo coverage is indexed in a way that helps venue selection instead of merely counting images.
- The system can generate a search-ready aggregate index without re-researching the data.
- Unknown or conflicting information is explicitly marked instead of guessed.

## Research Strategy

Phase 1 uses a semi-automated research pipeline. The system may assist with collection and normalization, but the final venue interpretation must remain structured and conservative. Bali wedding information is spread across official sites, brochures, hotel pages, venue pages, wedding directories, blogs, media features, and social platforms. A fully automated crawler would over-ingest stale, contradictory, or misleading information. The design therefore treats source preservation and explicit uncertainty as first-class requirements.

## Information Architecture

Phase 1 stores data in five layers with distinct responsibilities:

1. `seed registry`
   Candidate venue discovery and deduplication.
2. `source library`
   Raw source inventory with metadata about each page, brochure, gallery, or social page.
3. `venue canonical records`
   Normalized venue records used for comparison and decision-making.
4. `photo index`
   Structured image and gallery references tied to scene-level tags and usefulness labels.
5. `derived search index`
   Aggregated, website-ready output generated from the canonical records and photo index.

This separation prevents source sprawl from polluting the main venue records and allows the future website to consume a stable dataset.

## Venue Inclusion Rules

The candidate pool should include:

- Bali hotels and resorts with explicit wedding offerings
- Bali hotels and resorts with strong evidence of recurring wedding use
- Representative standalone wedding venues that are locally important or visually distinctive

The candidate pool should not include:

- Generic restaurants or event spaces with no strong wedding relevance
- Venues outside Bali
- Wedding vendors that are not venue operators

## Canonical Venue Record

Each venue is represented as a single canonical record. The canonical record is the primary comparison unit for the user.

### Identity Fields

- `id`
- `name_zh`
- `name_en_official`
- `brand_or_group`
- `venue_operator_type`
  - `hotel`
  - `resort`
  - `standalone_venue`
  - `villa_estate`
- `is_standalone`
- `region`
- `subarea`
- `official_website`
- `maps_url`
- `address_text`

### Venue-Type Fields

- `venue_types`
  Multi-select field with values such as:
  - `water-platform`
  - `chapel`
  - `cliffside`
  - `beach`
  - `lawn`
  - `garden`
  - `jungle`
  - `ballroom`
  - `villa-buyout`
  - `rooftop`
- `primary_visual_identity`
- `ceremony_space_types`
- `reception_space_types`

### Wedding-Fit Fields

- `supports_ceremony_only`
- `supports_ceremony_and_dinner`
- `supports_buyout`
- `supports_micro_wedding`
- `guest_capacity_ceremony_min`
- `guest_capacity_ceremony_max`
- `guest_capacity_dinner_min`
- `guest_capacity_dinner_max`
- `recommended_guest_size_band`
  - `2-20`
  - `21-50`
  - `51-80`
  - `81-120`
  - `120+`

### Pricing Fields

- `pricing_status`
  - `public_price_available`
  - `quote_required`
  - `unknown`
- `price_entries`
  List of normalized price records containing:
  - `label`
  - `currency`
  - `amount_min`
  - `amount_max`
  - `pricing_year`
  - `includes_stay`
  - `includes_decoration`
  - `includes_dinner`
  - `includes_tax_service`
  - `conditions_text`
  - `confidence`
    - `high`
    - `medium`
    - `low`
- `price_summary_text`
- `price_risk_level`
  - `low`
  - `medium`
  - `high`

### Rain Backup Fields

- `rain_backup_status`
  - `strong`
  - `medium`
  - `weak`
  - `unknown`
- `has_indoor_backup`
- `has_covered_backup`
- `backup_space_description`
- `backup_quality_notes`
- `weather_exposure_notes`

### Accommodation and Transport Fields

- `airport_drive_time_minutes_estimate`
- `transport_notes`
- `traffic_risk_level`
  - `low`
  - `medium`
  - `high`
  - `unknown`
- `onsite_accommodation_available`
- `onsite_room_inventory_notes`
- `nearby_accommodation_notes`
- `accommodation_fit`
  - `one_stop`
  - `workable_with_shuttles`
  - `fragmented`
  - `unknown`
- `guest_mobility_notes`

### Restrictions and Operations Fields

- `restriction_level`
  - `low`
  - `medium`
  - `high`
  - `unknown`
- `noise_cutoff_notes`
- `external_vendor_policy`
- `minimum_stay_requirement_notes`
- `minimum_spend_notes`
- `drone_policy_notes`
- `family_child_notes`
- `religious_or_space_use_notes`
- `operational_constraints_notes`

### Decision-Support Fields

- `style_tags`
- `price_band_normalized`
  - `budget`
  - `midrange`
  - `premium`
  - `luxury`
  - `ultra_luxury`
  Initial normalization rule:
  - `budget`: starting public ceremony package under USD 3,000
  - `midrange`: USD 3,000 to under USD 6,000
  - `premium`: USD 6,000 to under USD 10,000
  - `luxury`: USD 10,000 to under USD 18,000
  - `ultra_luxury`: USD 18,000 and above
  If pricing is quote-only or too incomplete to normalize, the field remains unset and the venue must carry `price_risk_level: high`.
- `best_for`
- `not_ideal_for`
- `key_strengths`
- `key_risks`
- `data_completeness`
  - `deep_complete`
  - `comparable_core_complete`
  - `initial_capture_only`
- `research_status`
  - `candidate`
  - `record_created`
  - `deep_research_complete`
  - `needs_price_followup`
  - `needs_photo_followup`
- `last_verified_at`
- `data_freshness`
  - `recent`
  - `possibly_outdated`
  - `clearly_outdated`
- `open_questions`

### Source Linkage Fields

- `source_ids`
- `photo_index_id`

## Source Library Model

Every source entry exists independently from the venue record so conflicting claims can coexist without corrupting the canonical record.

Each source entry should capture:

- `source_id`
- `venue_id`
- `source_type`
  - `official`
  - `platform_agency`
  - `editorial_case_study`
  - `social_inspiration`
- `source_name`
- `source_url`
- `captured_at`
- `content_date_if_known`
- `language`
- `evidence_categories`
  Such as `pricing`, `capacity`, `rain_backup`, `photos`, `restrictions`, `accommodation`
- `reliability_notes`
- `raw_excerpt_summary`

## Photo Index Model

Photos are treated as first-class research data rather than a loose appendix. The objective is not only to collect many images, but to collect images that help the user assess venue reality.

Each photo or gallery entry should capture:

- `photo_entry_id`
- `venue_id`
- `source_id`
- `page_url`
- `image_url_or_gallery_url`
- `image_type`
  - `official_wedding_gallery`
  - `official_hotel_gallery`
  - `real_wedding_feature`
  - `platform_listing_gallery`
  - `blog_feature`
  - `press_feature`
  - `social_post`
- `scene_tags`
  Multi-select values such as:
  - `water-platform`
  - `chapel-interior`
  - `chapel-exterior`
  - `cliffside-ceremony`
  - `beach-ceremony`
  - `garden-reception`
  - `ballroom-reception`
  - `jungle-view`
  - `guest-seating`
  - `floral-setup`
  - `entrance-procession`
  - `night-view`
  - `room`
  - `public-area`
  - `arrival-flow`
  - `rain-backup-space`
- `authenticity`
  - `official_promotional`
  - `real_wedding`
  - `unknown`
- `coverage_type`
  - `single_image`
  - `small_gallery`
  - `large_gallery`
  - `document_embedded`
- `decision_value`
  - `high`
  - `medium`
  - `low`
- `decision_notes`

Each venue also needs roll-up photo coverage fields:

- `photo_coverage_ceremony`
- `photo_coverage_reception`
- `photo_coverage_rain_backup`
- `photo_coverage_accommodation`
- `photo_reference_value_overall`

Coverage roll-up fields should use:

- `high`
- `medium`
- `low`
- `unknown`

## Classification System

The venue research system must support fast filtering across multiple independent axes.

### Geography

- `Uluwatu`
- `Nusa Dua`
- `Jimbaran`
- `Seminyak`
- `Canggu`
- `Ubud`
- `Sanur`
- Other Bali subareas as encountered

### Venue and Scenic Form

- water platform
- chapel
- cliffside
- beach
- lawn
- garden
- jungle
- ballroom
- villa buyout
- rooftop

### Guest Scale

- `2-20`
- `21-50`
- `51-80`
- `81-120`
- `120+`

### Price Band

The system should preserve raw pricing but also assign a normalized rough price band for quick filtering. Phase 1 must use these initial thresholds based on the starting public wedding package price in USD-equivalent:

- `budget`: under USD 3,000
- `midrange`: USD 3,000 to under USD 6,000
- `premium`: USD 6,000 to under USD 10,000
- `luxury`: USD 10,000 to under USD 18,000
- `ultra_luxury`: USD 18,000 and above

If the venue only has quote-based pricing or incomplete pricing that cannot be reliably normalized, the normalized price band remains blank and the venue must be marked as high price-risk.

### Rain Backup Strength

- `strong`
  Explicit indoor or quality covered backup with credible continuity
- `medium`
  Backup exists but the experience meaningfully degrades
- `weak`
  Backup is vague, temporary, highly compromised, or timing-dependent
- `unknown`

### Accommodation Fit

- `one_stop`
  Venue and guest stay experience are highly integrated
- `workable_with_shuttles`
  Nearby stay options exist but movement needs coordination
- `fragmented`
  Guests are likely to split across multiple stay clusters
- `unknown`

### Restriction Strength

- `low`
- `medium`
- `high`
- `unknown`

### Traffic Risk

- `low`
- `medium`
- `high`
- `unknown`

## Fast-Elimination Logic

The system is optimized to help the user remove poor-fit venues quickly. Each canonical record should support these elimination patterns:

- guest-count mismatch
- weak or unknown rain backup
- accommodation setup that is unfriendly for group stay
- hidden cost exposure through buyout, minimum stay, or minimum spend requirements
- low pricing clarity
- high operational restrictions
- low-value photo coverage despite strong marketing imagery

The canonical record therefore needs both structured flags and short human-readable judgment fields. A venue is not excluded solely because a field is unknown, but unknowns must raise explicit comparison risk.

## Research Workflow

Every venue should move through the same pipeline:

1. Add venue candidate to the seed registry.
2. Confirm venue identity and deduplicate aliases.
3. Capture official and non-official sources into the source library.
4. Extract core facts into the canonical venue record.
5. Build the photo index for wedding-relevant imagery.
6. Write human judgment fields such as `best_for`, `not_ideal_for`, `key_strengths`, and `key_risks`.
7. Assign completeness, freshness, and research status.
8. Generate derived search data.

## Reliability and Conflict Handling

The system must never hide disagreement between sources.

### Core Rules

- Unknown information stays unknown.
- Contradictory information is recorded as contradiction, not silently merged.
- Old pricing cannot be represented as current pricing unless there is explicit evidence.
- Ambiguous backup wording cannot be upgraded into strong backup.
- Beautiful but low-informational imagery cannot be treated as strong photo evidence.

### Price Handling

Price records must preserve:

- original wording
- normalized values
- year if known
- inclusions and conditions
- confidence score

If different sources disagree, the canonical record should present a conservative summary and store the conflict in notes rather than erasing the disagreement.

### Capacity Handling

Ceremony and dinner capacities must be stored separately. A venue that fits a ceremony may not fit a seated dinner. If capacities differ across sources, prefer the newer or more explicit source but keep the conflict note.

### Rain Backup Handling

Claims such as "backup available upon request" are insufficient for a `strong` rating without additional evidence of space quality and viability.

### Photo Authenticity Handling

Photo evidence should distinguish between:

- official promotional imagery
- real wedding imagery
- unknown or styled-shoot imagery

High-volume promotional images with little event reality should not produce a high overall photo reference value.

## File and Content Deliverables

Phase 1 should produce these repository-level deliverables:

- `data/venues/`
  One JSON file per venue canonical record
- `data/photos/`
  One JSON file per venue photo index
- `data/sources/`
  Source records and supporting metadata
- `data/derived/venues-index.json`
  Search-ready aggregate dataset for the future local website
- `content/venue-notes/`
  Readable venue summaries in Traditional Chinese with official English names preserved

The website phase should consume `data/derived/venues-index.json` and link back to the raw venue and source data as needed.

## Architecture for the Future Website

Phase 2 is not implemented here, but Phase 1 must support these views without changing the research model:

- overview table with filters for region, visual type, guest count, price band, rain backup, accommodation fit, and restriction level
- photo-first comparison view
- venue detail view with structured facts plus short narrative guidance
- source drill-down view
- unresolved questions view showing quote-required or incomplete venues

This is why Phase 1 must output both raw records and a derived aggregate index.

## Error Handling Principles

- Do not guess missing values.
- Do not flatten contradictions into fake certainty.
- Do not treat high image count as high decision usefulness by default.
- Do not lose source attribution during normalization.
- Do not allow duplicate venue records for the same property under alternate naming.

## Validation Requirements

Phase 1 must validate the dataset continuously.

### Schema Validation

Every venue, source, photo, and derived record must follow a stable schema.

### Required Field Validation

Every created venue record must include at least:

- venue identity
- region
- venue type
- source linkage
- last verified date
- research status

### Citation Integrity Validation

Important claims in a venue record must be traceable to one or more source entries.

### Derived Data Validation

The derived website index must preserve the essential decision fields from the canonical records.

### Photo Index Validation

Each photo entry must include a source, a type, at least one scene tag, and a decision-value label.

## Testing Strategy

Phase 1 implementation should be test-driven and should include:

- schema validation tests
- record-normalization tests
- deduplication tests for venue aliases
- derived-index generation tests
- validation tests for missing required fields
- photo-index integrity tests

The implementation should verify both data correctness and failure cases, especially contradiction handling and unknown-field preservation.

## Recommended Execution Order

Implementation should proceed in this order:

1. Define schemas for venue, source, photo, and derived records.
2. Create seed, source, venue, and photo storage layout.
3. Implement validation and normalization utilities.
4. Implement canonical venue record generation.
5. Implement photo index generation and roll-up scoring.
6. Implement derived search index generation.
7. Add human-readable venue notes.
8. Populate the first researched venue batch and validate the workflow.

## Design Boundaries

This design deliberately stops before building the local website. The correct next step after Phase 1 design approval is to write an implementation plan for the research database. After the research database exists and is populated enough to validate the model, a separate spec should define the local search website.
