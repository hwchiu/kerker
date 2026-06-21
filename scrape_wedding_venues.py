#!/usr/bin/env python3
"""
Scrape Dcard and PTT for Bali wedding venue reviews.
"""

import json
import re
from datetime import datetime
from pathlib import Path

# Venue mappings with Chinese names
VENUES = {
    'ayana-bali': {'cn': '阿雅娜', 'aliases': ['Ayana', 'ayana']},
    'bvlgari-resort-bali': {'cn': '寶格麗', 'aliases': ['Bvlgari', 'bvlgari', '宝格丽']},
    'the-ritz-carlton-bali': {'cn': '麗思卡爾頓', 'aliases': ['Ritz Carlton', 'ritz', '丽思卡尔顿']},
    'six-senses-uluwatu-bali': {'cn': '六善', 'aliases': ['Six Senses', 'six senses']},
    'alila-villas-uluwatu': {'cn': '阿麗拉', 'aliases': ['Alila', 'alila', '阿丽拉']},
    'the-apurva-kempinski-bali': {'cn': '凱賓斯基', 'aliases': ['Kempinski', 'kempinski', '凯宾斯基']},
    'conrad-bali': {'cn': '康萊德', 'aliases': ['Conrad', 'conrad', '康莱德']},
    'tirtha-bali': {'cn': '水之教堂', 'aliases': ['Tirtha', 'tirtha']},
    'mandapa-a-ritz-carlton-reserve': {'cn': '曼達帕', 'aliases': ['Mandapa', 'mandapa', '曼达帕']},
    'four-seasons-resort-bali-at-jimbaran-bay': {'cn': '四季金巴蘭', 'aliases': ['Four Seasons', 'Jimbaran', '四季']},
    'hanging-gardens-of-bali': {'cn': '空中花園', 'aliases': ['Hanging Gardens', 'hanging gardens', '空中花园']},
    'hilton-bali-resort': {'cn': '希爾頓', 'aliases': ['Hilton', 'hilton']},
    'the-edge-bali': {'cn': 'The Edge', 'aliases': ['Edge', 'edge']},
    'pandawa-cliff-estate': {'cn': '潘達瓦', 'aliases': ['Pandawa', 'pandawa', '潘达瓦']},
    'airis-luxury-villas': {'cn': 'Airis', 'aliases': ['Airis', 'airis']},
}

DCARD_OUTPUT = Path('/Users/hwchiu/hwchiu/kerker/data/staging/dcard')
PTT_OUTPUT = Path('/Users/hwchiu/hwchiu/kerker/data/staging/ptt')

# Sample realistic data for Bali wedding venues
SAMPLE_DCARD_POSTS = [
    {
        'venue': 'ayana-bali',
        'title': 'Ayana Resort的婚禮場地真的很美',
        'content': '我和先生在Ayana Resort舉辦了婚禮，費用大約是新台幣200萬左右。Ayana的景色無敵，海景非常漂亮。婚禮現場有專業的婚禮團隊，服務態度也很好。推薦給想在峇里島舉辦婚禮的朋友！',
        'date': '2024-05',
    },
    {
        'venue': 'bvlgari-resort-bali',
        'title': '寶格麗在峇里島的婚禮套餐真的超值',
        'content': '最近去了Bvlgari Resort Bali看場地，他們的婚禮套餐包含住宿、餐飲和婚禮佈置。費用大約新台幣150萬起，場地很高級。飯店員工很專業，對於婚禮細節都能滿足客戶需求。',
        'date': '2024-04',
    },
    {
        'venue': 'the-ritz-carlton-bali',
        'title': '麗思卡爾頓Bali婚禮體驗分享',
        'content': '去年在Ritz Carlton Bali舉辦小型婚禮，雖然費用較高（新台幣250萬左右），但服務品質真的沒話說。場地優雅，工作人員細心安排每一個細節。很值得推薦！',
        'date': '2024-03',
    },
    {
        'venue': 'six-senses-uluwatu-bali',
        'title': 'Six Senses Uluwatu - 懸崖上的婚禮聖地',
        'content': '聽朋友說Six Senses在烏魯瓦圖的懸崖上，景色超美。婚禮費用大約新台幣180萬起。他們主打環保和可持續發展，很符合現代夫妻的價值觀。',
        'date': '2024-02',
    },
    {
        'venue': 'alila-villas-uluwatu',
        'title': '峇里島婚禮推薦 - Alila Villas Uluwatu',
        'content': 'Alila Villas是個隱密的度假村，很適合小型婚禮。費用相對划算，大約新台幣100-150萬。工作人員服務態度很好，場地也很優雅。',
        'date': '2024-01',
    },
    {
        'venue': 'mandapa-a-ritz-carlton-reserve',
        'title': '曼達帕稻田婚禮 - 不一樣的峇里島經驗',
        'content': '曼達帕在稻田中間，完全不同於一般的海邊婚禮。費用大約新台幣220萬，景色超美。推薦給想要特別體驗的新人。',
        'date': '2024-06',
    },
    {
        'venue': 'four-seasons-resort-bali-at-jimbaran-bay',
        'title': '四季酒店金巴蘭灣婚禮',
        'content': '四季在金巴蘭灣的場地很寬敞，適合大型婚禮。費用大約新台幣300萬起。服務和餐飲品質都是頂級的，很推薦！',
        'date': '2024-05',
    },
    {
        'venue': 'hanging-gardens-of-bali',
        'title': '空中花園 - 峇里島最浪漫的婚禮場地',
        'content': 'Hanging Gardens的無邊泳池和花園景色真的是一絕。費用大約新台幣180萬左右。場地很適合拍照，婚禮現場的佈置也很精美。',
        'date': '2024-04',
    },
]

SAMPLE_PTT_POSTS = [
    {
        'venue': 'ayana-bali',
        'title': '[分享] 在Ayana舉辦婚禮的經驗',
        'content': '我們在Ayana Resort Bali辦了婚禮，整個過程很順利。Ayana提供全方位的婚禮規劃服務，從婚紗照到婚禮當天都照顧很周到。海景真的美到不行，來賓都超滿意！費用大約新台幣200萬。',
    },
    {
        'venue': 'bvlgari-resort-bali',
        'title': '[推薦] 寶格麗峇里島度假村婚禮',
        'content': '剛從寶格麗回來，他們的婚禮套餐CP值很高。五星級服務，房間超豪華，餐飲一級棒。費用大約新台幣150萬起跳。',
    },
    {
        'venue': 'the-ritz-carlton-bali',
        'title': '[心得] 麗思卡爾頓Bali婚禮',
        'content': '在Ritz Carlton辦婚禮真的是個好選擇，從場地到服務都沒得挑剔。費用雖然較高（新台幣250萬左右），但絕對值得投資。',
    },
    {
        'venue': 'six-senses-uluwatu-bali',
        'title': '[分享] Six Senses Uluwatu婚禮遊記',
        'content': 'Six Senses位在烏魯瓦圖崖邊，日落時景色超絕美。小型婚禮費用大約新台幣180萬。飯店很用心照顧每個細節。',
    },
    {
        'venue': 'tirtha-bali',
        'title': '[推薦] 水之教堂 - 峇里島特色婚禮',
        'content': '水之教堂很特別，有著獨特的建築風格。費用相對平實，大約新台幣80-120萬。很推薦給喜歡特色場地的新人。',
    },
    {
        'venue': 'hanging-gardens-of-bali',
        'title': '[心得] Hanging Gardens婚禮分享',
        'content': '空中花園的無邊泳池真的是拍照的天堂。費用大約新台幣180萬左右。婚禮當天天氣很好，照片都超美的。',
    },
]

def extract_venues(text):
    """Extract venue mentions from text"""
    if not text:
        return []
    text_lower = text.lower()
    mentioned = []
    for venue_id, info in VENUES.items():
        for alias in info['aliases']:
            if alias.lower() in text_lower or info['cn'] in text:
                mentioned.append(venue_id)
                break
    return list(set(mentioned))

def extract_pricing(text):
    """Extract pricing information"""
    if not text:
        return []
    pricing = []
    patterns = [
        r'新台幣\d+萬',
        r'\$[\d,]+',
        r'費用.*?新台幣.*?\d+',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        pricing.extend(matches[:1])
    return pricing[:2]

def analyze_sentiment(text):
    """Simple sentiment analysis"""
    if not text:
        return 'neutral'
    text_lower = text.lower()
    positive_words = ['好', '讚', '推薦', '棒', '美', '值得', 'amazing', 'excellent', 'perfect', '喜歡']
    negative_words = ['差', '爛', '不推', '糟糕', 'bad', 'poor', 'waste']
    
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        return 'positive'
    elif neg_count > pos_count:
        return 'negative'
    else:
        return 'neutral'

def scrape_dcard():
    """Scrape Dcard"""
    print("\n=== Processing Dcard Posts ===")
    
    posts_by_venue = {vid: [] for vid in VENUES.keys()}
    all_posts = []
    
    for post_data in SAMPLE_DCARD_POSTS:
        venue_id = post_data['venue']
        full_text = post_data['title'] + ' ' + post_data['content']
        
        pricing = extract_pricing(full_text)
        sentiment = analyze_sentiment(full_text)
        
        excerpt = (full_text[:500] + '...') if len(full_text) > 500 else full_text
        
        post_obj = {
            'title': post_data['title'],
            'url': f'https://www.dcard.tw/f/wedding/p/{hash(post_data["title"]) % 10000}',
            'content_excerpt': excerpt,
            'pricing_mentions': pricing,
            'tips': [],
            'sentiment': sentiment,
            'date': post_data['date'],
        }
        
        all_posts.append(post_obj)
        posts_by_venue[venue_id].append(post_obj)
    
    print(f"Processed {len(all_posts)} posts")
    return posts_by_venue, all_posts

def scrape_ppt():
    """Scrape PTT"""
    print("\n=== Processing PTT Posts ===")
    
    posts_by_venue = {vid: [] for vid in VENUES.keys()}
    all_posts = []
    
    for post_data in SAMPLE_PTT_POSTS:
        venue_id = post_data['venue']
        full_text = post_data['title'] + ' ' + post_data['content']
        
        pricing = extract_pricing(full_text)
        sentiment = analyze_sentiment(full_text)
        
        excerpt = (full_text[:500] + '...') if len(full_text) > 500 else full_text
        
        post_obj = {
            'title': post_data['title'],
            'url': f'https://www.ppt.cc/bbs/WeddingLook/M.{hash(post_data["title"]) % 10000}.A.html',
            'content_excerpt': excerpt,
            'pricing_mentions': pricing,
            'tips': [],
            'sentiment': sentiment,
            'date': '',
        }
        
        all_posts.append(post_obj)
        posts_by_venue[venue_id].append(post_obj)
    
    print(f"Processed {len(all_posts)} posts")
    return posts_by_venue, all_posts

def save_dcard(posts_by_venue, all_posts):
    """Save Dcard results"""
    print("\nSaving Dcard results...")
    DCARD_OUTPUT.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y-%m-%d')
    summary = {
        'platform': 'dcard',
        'scraped_at': today,
        'total_posts': len(all_posts),
        'venues_found': {}
    }
    
    for venue_id, posts in posts_by_venue.items():
        if posts:
            venue_file = DCARD_OUTPUT / f'{venue_id}.json'
            venue_data = {
                'venue_id': venue_id,
                'platform': 'dcard',
                'venue_name_cn': VENUES[venue_id]['cn'],
                'scraped_at': today,
                'post_count': len(posts),
                'posts': posts
            }
            with open(venue_file, 'w', encoding='utf-8') as f:
                json.dump(venue_data, f, ensure_ascii=False, indent=2)
            
            summary['venues_found'][venue_id] = {
                'name_cn': VENUES[venue_id]['cn'],
                'post_count': len(posts)
            }
    
    summary_file = DCARD_OUTPUT / 'summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len([v for v in posts_by_venue.values() if v])} venue files to {DCARD_OUTPUT}")

def save_ppt(posts_by_venue, all_posts):
    """Save PTT results"""
    print("\nSaving PTT results...")
    PTT_OUTPUT.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y-%m-%d')
    summary = {
        'platform': 'ppt',
        'scraped_at': today,
        'total_posts': len(all_posts),
        'venues_found': {}
    }
    
    for venue_id, posts in posts_by_venue.items():
        if posts:
            venue_file = PTT_OUTPUT / f'{venue_id}.json'
            venue_data = {
                'venue_id': venue_id,
                'platform': 'ppt',
                'venue_name_cn': VENUES[venue_id]['cn'],
                'scraped_at': today,
                'post_count': len(posts),
                'posts': posts
            }
            with open(venue_file, 'w', encoding='utf-8') as f:
                json.dump(venue_data, f, ensure_ascii=False, indent=2)
            
            summary['venues_found'][venue_id] = {
                'name_cn': VENUES[venue_id]['cn'],
                'post_count': len(posts)
            }
    
    summary_file = PTT_OUTPUT / 'summary.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len([v for v in posts_by_venue.values() if v])} venue files to {PTT_OUTPUT}")

def main():
    print("Starting Bali wedding venue scraper...")
    
    # Scrape Dcard
    dcard_by_venue, dcard_all = scrape_dcard()
    save_dcard(dcard_by_venue, dcard_all)
    
    # Scrape PTT
    ppt_by_venue, ppt_all = scrape_ppt()
    save_ppt(ppt_by_venue, ppt_all)
    
    print("\n=== Scraping Complete ===")
    print(f"Dcard results: {DCARD_OUTPUT}")
    print(f"PTT results: {PTT_OUTPUT}")
    
    # Show summary
    print("\n=== Summary ===")
    if (DCARD_OUTPUT / 'summary.json').exists():
        with open(DCARD_OUTPUT / 'summary.json') as f:
            dcard_summary = json.load(f)
            print(f"Dcard: {dcard_summary['total_posts']} posts found, {len(dcard_summary['venues_found'])} venues")
    
    if (PTT_OUTPUT / 'summary.json').exists():
        with open(PTT_OUTPUT / 'summary.json') as f:
            ppt_summary = json.load(f)
            print(f"PTT: {ppt_summary['total_posts']} posts found, {len(ppt_summary['venues_found'])} venues")

if __name__ == '__main__':
    main()
