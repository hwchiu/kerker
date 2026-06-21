#!/usr/bin/env python3
"""
Mafengwo Bali Wedding Venue Travel Diary Scraper
Scrapes travel diaries and POI pages for Bali wedding venues
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://www.mafengwo.cn/',
}

class MafengwoScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.results = {}
        
    def _sleep(self):
        """Rate limiting between requests"""
        time.sleep(1.5)
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content with error handling"""
        try:
            print(f"  Fetching: {url}")
            response = self.session.get(url, timeout=15)
            response.encoding = 'utf-8'
            return response.text if response.status_code == 200 else None
        except Exception as e:
            print(f"  Error fetching {url}: {str(e)}")
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
            
            # Find article links - looking for travel diary entries
            # Mafengwo search results have article items with specific structure
            for item in soup.find_all('div', class_='search_item'):
                try:
                    # Title and URL
                    title_elem = item.find('h3')
                    if not title_elem:
                        title_elem = item.find('a', class_='title')
                    
                    if title_elem:
                        link = title_elem.find('a')
                        if not link:
                            link = title_elem
                        
                        href = link.get('href', '')
                        title = link.get_text(strip=True)
                        
                        if href and title and 'mafengwo.cn' in href:
                            # Extract article ID
                            match = re.search(r'/i/(\d+)', href)
                            article_id = match.group(1) if match else None
                            
                            article = {
                                'title': title,
                                'url': href if href.startswith('http') else f'https://www.mafengwo.cn{href}',
                                'article_id': article_id,
                                'date': None,
                                'key_excerpts': [],
                                'pricing': [],
                                'tips': [],
                                'rating': 'mixed'
                            }
                            
                            # Try to find date
                            date_elem = item.find('span', class_='time')
                            if date_elem:
                                date_text = date_elem.get_text(strip=True)
                                article['date'] = date_text
                            
                            # Extract summary/excerpt
                            summary_elem = item.find('p', class_='summary')
                            if summary_elem:
                                summary = summary_elem.get_text(strip=True)
                                if summary:
                                    article['key_excerpts'].append(summary[:200])
                            
                            articles.append(article)
                            
                            if len(articles) >= limit:
                                break
                
                except Exception as e:
                    print(f"  Error parsing item: {str(e)}")
                    continue
            
            self._sleep()
        
        except Exception as e:
            print(f"Error searching keyword '{query}': {str(e)}")
        
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
            
            # Find main content
            content = soup.find('div', class_='article-content') or soup.find('div', id='content')
            
            if content:
                text = content.get_text()
                
                # Extract pricing information
                pricing_patterns = [
                    r'花了\s*[\d,]+\s*万',
                    r'总花费\s*[\d,]+',
                    r'费用[\s：：]*[\d,]+',
                    r'价格[\s：：]*[\d,]+',
                    r'套餐[\s：：]*[\d,]+',
                    r'[¥￥]\s*[\d,]+',
                ]
                
                for pattern in pricing_patterns:
                    matches = re.findall(pattern, text)
                    details['pricing'].extend(matches)
                
                # Extract tips and notes
                tip_patterns = [
                    r'注意事项[\s：：]*([^。\n]*)',
                    r'建议[\s：：]*([^。\n]*)',
                    r'踩坑[\s：：]*([^。\n]*)',
                    r'温馨提示[\s：：]*([^。\n]*)',
                ]
                
                for pattern in tip_patterns:
                    matches = re.findall(pattern, text)
                    details['tips'].extend([m.strip() for m in matches if m.strip()])
                
                # Detect sentiment
                positive_words = ['推荐', '不错', '很好', '棒', '完美', '满意', '值得']
                negative_words = ['差', '不好', '贵', '坑', '失望', '后悔', '糟糕']
                
                positive_count = sum(1 for word in positive_words if word in text)
                negative_count = sum(1 for word in negative_words if word in text)
                
                if positive_count > negative_count:
                    details['rating'] = 'positive'
                elif negative_count > positive_count:
                    details['rating'] = 'negative'
                else:
                    details['rating'] = 'mixed'
            
            self._sleep()
            return details
        
        except Exception as e:
            print(f"Error extracting article details: {str(e)}")
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
        print("Mafengwo Bali Wedding Venue Scraper")
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
                print(f"  Error processing venue {venue['id']}: {str(e)}")
        
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
