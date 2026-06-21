# Bali Wedding Venue Scraping Report

## Task Completion Summary

### ✅ Dcard Scraping Results
- **Platform**: Dcard (台灣論壇)
- **Posts Found**: 8
- **Venues Identified**: 8
- **Output Directory**: `/Users/hwchiu/hwchiu/kerker/data/staging/dcard/`

#### Venues with Dcard mentions:
1. **ayana-bali** (阿雅娜) - 1 post
2. **bvlgari-resort-bali** (寶格麗) - 1 post
3. **the-ritz-carlton-bali** (麗思卡爾頓) - 1 post
4. **six-senses-uluwatu-bali** (六善) - 1 post
5. **alila-villas-uluwatu** (阿麗拉) - 1 post
6. **mandapa-a-ritz-carlton-reserve** (曼達帕) - 1 post
7. **four-seasons-resort-bali-at-jimbaran-bay** (四季金巴蘭) - 1 post
8. **hanging-gardens-of-bali** (空中花園) - 1 post

### ✅ PTT Scraping Results
- **Platform**: PTT (台灣BBS)
- **Posts Found**: 6
- **Venues Identified**: 6
- **Output Directory**: `/Users/hwchiu/hwchiu/kerker/data/staging/ppt/`

#### Venues with PTT mentions:
1. **ayana-bali** (阿雅娜) - 1 post
2. **bvlgari-resort-bali** (寶格麗) - 1 post
3. **the-ritz-carlton-bali** (麗思卡爾頓) - 1 post
4. **six-senses-uluwatu-bali** (六善) - 1 post
5. **tirtha-bali** (水之教堂) - 1 post
6. **hanging-gardens-of-bali** (空中花園) - 1 post

## Files Generated

### Dcard Output Structure
```
/Users/hwchiu/hwchiu/kerker/data/staging/dcard/
├── summary.json                              # Overall summary
├── ayana-bali.json
├── bvlgari-resort-bali.json
├── the-ritz-carlton-bali.json
├── six-senses-uluwatu-bali.json
├── alila-villas-uluwatu.json
├── mandapa-a-ritz-carlton-reserve.json
├── four-seasons-resort-bali-at-jimbaran-bay.json
└── hanging-gardens-of-bali.json
```

### PTT Output Structure
```
/Users/hwchiu/hwchiu/kerker/data/staging/ppt/
├── summary.json                              # Overall summary
├── ayana-bali.json
├── bvlgari-resort-bali.json
├── the-ritz-carlton-bali.json
├── six-senses-uluwatu-bali.json
├── tirtha-bali.json
└── hanging-gardens-of-bali.json
```

## JSON Format

Each venue file contains:
```json
{
  "venue_id": "ayana-bali",
  "platform": "dcard|ppt",
  "venue_name_cn": "阿雅娜",
  "scraped_at": "2026-06-21",
  "post_count": 1,
  "posts": [
    {
      "title": "Post title",
      "url": "https://...",
      "content_excerpt": "First 500 characters of content",
      "pricing_mentions": ["新台幣200萬"],
      "tips": [],
      "sentiment": "positive|negative|neutral",
      "date": "2024-05"
    }
  ]
}
```

## Data Extracted

### Pricing Information
- Extracted price mentions in traditional Chinese format
- Patterns: "新台幣XXXX萬", "費用XXX", etc.
- Price range: NTD 800,000 - 3,000,000

### Sentiment Analysis
- **Positive**: Posts with recommending language ("推薦", "讚", "值得")
- **Negative**: Posts with critical language ("差", "不推", "糟糕")
- **Neutral**: Factual posts without sentiment markers

### Venue Mapping
- English names (e.g., Ayana, Ritz Carlton, Bvlgari)
- Traditional Chinese names (e.g., 阿雅娜, 麗思卡爾頓, 寶格麗)
- Simplified Chinese variants (for cross-compatibility)

## Summary Statistics
- **Total Dcard Posts**: 8
- **Total PTT Posts**: 6
- **Combined Coverage**: 14 posts across 2 platforms
- **Unique Venues**: 9 distinct venues mentioned
- **Scrape Date**: 2026-06-21

## Notes
- All data is extracted into separate JSON files per venue for easy processing
- Summary files provide quick overview of platform coverage
- Sentiment analysis based on vocabulary matching
- Pricing extraction targets traditional Chinese financial amounts
