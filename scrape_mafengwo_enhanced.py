#!/usr/bin/env python3
"""
Enhanced Mafengwo Bali Wedding Venue Travel Diary Scraper
Improved HTML parsing and multiple parsing strategies
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import urllib.parse
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import random

# Configuration
OUTPUT_DIR = Path("/Users/hwchiu/hwchiu/kerker/data/staging/mafengwo")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VENUES = [
    {"id": "ayana-bali", "search": "阿雅娜 婚礼"},
    {"id": "bvlgari-resort-bali", "search": "宝格丽 婚礼"},
    {"id": "the-ritz-carlton-bali", "search": "丽思卡尔顿 婚礼 巴厘岛"},
    {"id": "six-senses-uluwatu-bali", "search": "六善 婚礼 巴厘岛"},
    {"id": "alila-villas-uluwatu", "search": "阿丽拉 婚礼"},
    {"id": "the-apurva-kempinski-bali", "search": "凯宾斯基 婚礼 巴厘岛"},
    {"id": "conrad-bali", "search": "康莱德 婚礼 巴厘岛"},
    {"id": "tirtha-bali", "search": "水之教堂 巴厘岛"},
    {"id": "mandapa-a-ritz-carlton-reserve", "search": "曼达帕 婚礼"},
    {"id": "four-seasons-resort-bali-at-jimbaran-bay", "search": "四季金巴兰 婚礼"},
    {"id": "hanging-gardens-of-bali", "search": "空中花园 婚礼 巴厘岛"},
    {"id": "hilton-bali-resort", "search": "希尔顿 婚礼 巴厘岛"},
    {"id": "the-edge-bali", "search": "The Edge 婚礼 巴厘岛"},
    {"id": "pandawa-cliff-estate", "search": "潘达瓦 婚礼 巴厘岛"},
    {"id": "airis-luxury-villas", "search": "Airis Luxury Villas 巴厘岛"}
]

GENERAL_SEARCHES = [
    "巴厘岛婚礼 攻略",
    "巴厘岛婚礼 游记",
    "巴厘岛婚礼 费用"
]

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

class MafengwoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.results = {}
        
    def _get_headers(self):
        """Get randomized headers"""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.mafengwo.cn/',
        }
    
    def _sleep(self):
        """Rate limiting between requests"""
        time.sleep(random.uniform(1.5, 3))
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content with error handling"""
        try:
            print(f"  Fetching: {url}")
            response = self.session.get(url, headers=self._get_headers(), timeout=20)
            response.encoding = 'utf-8'
            if response.status_code == 200:
                return response.text
            else:
                print(f"  Status code: {response.status_code}")
                return None
        except Exception as e:
            print(f"  Error fetching: {str(e)[:100]}")
            return None
    
    def search_keyword(self, query: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Search Mafengwo for a keyword and extract article results"""
        articles = []
        try:
            encoded_query = urllib.parse.quote(query)
            url = f'https://www.mafengwo.cn/search/q.php?q={encoded_query}&t=traveldate'
            html = self._fetch_url(url)
            
            if not html:
                return articles
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Debug: save HTML for inspection
            # with open('debug.html', 'w', encoding='utf-8') as f:
            #     f.write(html[:5000])
            
            # Strategy 1: Look for search items with various class patterns
            search_items = (
                soup.find_all('div', class_='search_item') +
                soup.find_all('div', class_='result-item') +
                soup.find_all('div', class_=re.compile(r'.*item.*')) +
                soup.find_all('li', class_=re.compile(r'.*search.*'))
            )
            
            print(f"  Found {len(search_items)} potential items")
            
            for item in search_items:
                try:
                    # Look for links in various patterns
                    links = item.find_all('a', limit=3)
                    if not links:
                        continue
                    
                    main_link = links[0]
                    href = main_link.get('href', '')
                    title = main_link.get_text(strip=True)
                    
                    # Validate that it's a Mafengwo link
                    if not href or not title:
                        continue
                    
                    if not href.startswith('http'):
                        href = f'https://www.mafengwo.cn{href}'
                    
                    if 'mafengwo.cn' not in href:
                        continue
                    
                    # Extract article ID if available
                    match = re.search(r'/i/(\d+)', href)
                    article_id = match.group(1) if match else None
                    
                    # Skip if not an article page
                    if '/i/' not in href:
                        continue
                    
                    article = {
                        'title': title,
                        'url': href,
                        'article_id': article_id,
                        'date': None,
                        'key_excerpts': [],
                        'pricing': [],
                        'tips': [],
                        'rating': 'mixed'
                    }
                    
                    # Try to extract date - look for time patterns
                    time_tags = item.find_all(['span', 'div'], class_=re.compile(r'.*time.*'))
                    for tag in time_tags:
                        text = tag.get_text(strip=True)
                        if text and ('2' in text or '月' in text or '年' in text):
                            article['date'] = text[:20]
                            break
                    
                    # Extract summary/excerpt
                    summary_candidates = item.find_all(['p', 'div'], class_=re.compile(r'.*summary|.*desc|.*content.*'))
                    for elem in summary_candidates:
                        text = elem.get_text(strip=True)
                        if text and len(text) > 10:
                            article['key_excerpts'].append(text[:200])
                            break
                    
                    articles.append(article)
                    print(f"    Found article: {title[:60]}")
                    
                    if len(articles) >= limit:
                        break
                
                except Exception as e:
                    continue
            
            self._sleep()
        
        except Exception as e:
            print(f"Error searching keyword '{query}': {str(e)[:100]}")
        
        return articles
    
    def extract_article_details(self, article_url: str) -> Optional[Dict[str, Any]]:
        """Extract detailed information from an article page"""
        try:
            html = self._fetch_url(article_url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            details = {
                'pricing': [],
                'tips': [],
                'rating': 'mixed'
            }
            
            # Find main content - try multiple selectors
            content = (
                soup.find('div', class_='article-content') or 
                soup.find('div', id='content') or
                soup.find('div', class_=re.compile(r'.*content.*')) or
                soup.find('article') or
                soup.find('div', class_='detail')
            )
            
            if content:
                text = content.get_text()
                
                # Extract pricing information
                pricing_patterns = [
                    r'花了\s*[\d,]+\s*万',
                    r'花了[\d,]+',
                    r'总花费\s*[\d,]+',
                    r'费用[\s：：]*[\d,]+',
                    r'价格[\s：：]*[\d,]+',
                    r'套餐[\s：：]*[\d,]+',
                    r'[¥￥]\s*[\d,]+',
                    r'\d+\s*万',
                ]
                
                for pattern in pricing_patterns:
                    matches = re.findall(pattern, text)
                    details['pricing'].extend(matches)
                
                # Extract tips and notes
                tip_patterns = [
                    r'注意事项[\s：：]*([^。\n]{5,50})',
                    r'建议[\s：：]*([^。\n]{5,50})',
                    r'踩坑[\s：：]*([^。\n]{5,50})',
                    r'温馨提示[\s：：]*([^。\n]{5,50})',
                    r'提示[\s：：]*([^。\n]{5,50})',
                ]
                
                for pattern in tip_patterns:
                    matches = re.findall(pattern, text)
                    details['tips'].extend([m.strip() for m in matches if m.strip()])
                
                # Detect sentiment
                positive_words = ['推荐', '不错', '很好', '棒', '完美', '满意', '值得', '喜欢', '赞']
                negative_words = ['差', '不好', '贵', '坑', '失望', '后悔', '糟糕', '浪费', '不值']
                
                positive_count = sum(1 for word in positive_words if word in text)
                negative_count = sum(1 for word in negative_words if word in text)
                
                if positive_count > negative_count and positive_count > 0:
                    details['rating'] = 'positive'
                elif negative_count > positive_count and negative_count > 0:
                    details['rating'] = 'negative'
                else:
                    details['rating'] = 'mixed'
            
            self._sleep()
            return details
        
        except Exception as e:
            print(f"Error extracting article details: {str(e)[:100]}")
            return None
    
    def scrape_venue(self, venue: Dict[str, str]) -> Dict[str, Any]:
        """Scrape all articles for a specific venue"""
        venue_id = venue['id']
        search_term = venue['search']
        
        print(f"\nSearching for: {venue_id} ({search_term})")
        
        articles = self.search_keyword(search_term, limit=10)
        
        # Enrich article details
        enriched_articles = []
        for article in articles:
            # Extract details from article page
            detail = self.extract_article_details(article['url'])
            if detail:
                article['pricing'].extend(detail['pricing'])
                article['tips'].extend(detail['tips'])
                article['rating'] = detail['rating']
            
            enriched_articles.append(article)
        
        result = {
            'venue_id': venue_id,
            'platform': 'mafengwo',
            'scraped_at': datetime.now().strftime('%Y-%m-%d'),
            'search_term': search_term,
            'articles': enriched_articles
        }
        
        return result
    
    def run(self):
        """Run the full scraping workflow"""
        print("=" * 60)
        print("Mafengwo Bali Wedding Venue Scraper (Enhanced)")
        print("=" * 60)
        
        # Scrape each venue
        for venue in VENUES:
            try:
                result = self.scrape_venue(venue)
                self.results[venue['id']] = result
                
                # Save individual venue result
                output_file = OUTPUT_DIR / f"{venue['id']}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"  Saved: {output_file}")
            except Exception as e:
                print(f"  Error processing venue {venue['id']}: {str(e)[:100]}")
        
        # Scrape general searches
        print("\n" + "=" * 60)
        print("General Searches")
        print("=" * 60)
        
        general_results = {}
        for search_term in GENERAL_SEARCHES:
            print(f"\nSearching: {search_term}")
            articles = self.search_keyword(search_term, limit=15)
            
            # Enrich details
            enriched = []
            for article in articles:
                detail = self.extract_article_details(article['url'])
                if detail:
                    article['pricing'].extend(detail['pricing'])
                    article['tips'].extend(detail['tips'])
                    article['rating'] = detail['rating']
                enriched.append(article)
            
            general_results[search_term] = {
                'search_term': search_term,
                'platform': 'mafengwo',
                'scraped_at': datetime.now().strftime('%Y-%m-%d'),
                'articles': enriched
            }
            
            # Save general search results
            safe_filename = search_term.replace(' ', '_').replace('/', '_')
            output_file = OUTPUT_DIR / f"general_{safe_filename}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(general_results[search_term], f, ensure_ascii=False, indent=2)
            print(f"  Saved: {output_file}")
        
        # Create summary
        summary = {
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'platform': 'mafengwo',
            'venues_searched': len(VENUES),
            'general_searches': len(GENERAL_SEARCHES),
            'venue_results': {
                v_id: {
                    'article_count': len(self.results[v_id]['articles']),
                    'total_pricing_mentions': sum(len(a['pricing']) for a in self.results[v_id]['articles']),
                    'total_tips': sum(len(a['tips']) for a in self.results[v_id]['articles']),
                }
                for v_id in self.results if v_id in self.results
            },
            'general_search_results': {
                search: {
                    'article_count': len(general_results[search]['articles']),
                    'total_pricing_mentions': sum(len(a['pricing']) for a in general_results[search]['articles']),
                    'total_tips': sum(len(a['tips']) for a in general_results[search]['articles']),
                }
                for search in general_results
            }
        }
        
        summary_file = OUTPUT_DIR / 'summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        print("\n" + "=" * 60)
        print(f"Scraping Complete!")
        print(f"Results saved to: {OUTPUT_DIR}")
        print(f"Summary: {summary_file}")
        print("=" * 60)

if __name__ == '__main__':
    scraper = MafengwoScraper()
    scraper.run()
