#!/usr/bin/env python3
"""
Enhanced Zhihu Scraper with Proxy & Cookie Support
This script is designed to scrape Zhihu when access is available.
Requires: requests, beautifulsoup4, selenium (optional for JS-heavy content)
"""

import requests
import json
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin
from typing import Dict, List, Any, Optional
import os
import sys

class EnhancedZhihuScraper:
    """
    Scraper with support for:
    - Proxy rotation
    - Custom cookies
    - Rate limiting
    - Retry logic
    """
    
    def __init__(self, output_dir: str, cookies_file: Optional[str] = None, proxy: Optional[str] = None):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.proxy = proxy
        self.max_retries = 3
        self.timeout = 15
        
        # Setup proxies if provided
        if proxy:
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }
        
        # Load cookies if provided
        if cookies_file and os.path.exists(cookies_file):
            with open(cookies_file, 'r') as f:
                cookies = json.load(f)
                self.session.cookies.update(cookies)
        
        # Browser-like headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
    
    def get_with_retry(self, url: str, **kwargs) -> Optional[requests.Response]:
        """GET request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(url, timeout=self.timeout, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"  Retry {attempt + 1}/{self.max_retries} after {wait_time}s (Error: {type(e).__name__})")
                    time.sleep(wait_time)
                else:
                    print(f"  Failed after {self.max_retries} attempts: {e}")
                    return None
    
    def search_web(self, query: str) -> List[Dict[str, Any]]:
        """Search via web interface with proxy support."""
        try:
            encoded_query = quote(query)
            url = f'https://www.zhihu.com/search?q={encoded_query}&type=content'
            
            resp = self.get_with_retry(url)
            if not resp:
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            results = []
            
            # Extract results from various possible structures
            for item in soup.find_all(['article', 'div', 'li'], class_=re.compile(r'(Result|Item|Card|SearchResult)', re.I)):
                # Try to find title and link
                link_elem = item.find('a', href=True)
                title_elem = item.find(['h1', 'h2', 'h3', 'div'], class_=re.compile(r'Title', re.I))
                
                if not title_elem:
                    title_elem = link_elem
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)[:200]
                    href = link_elem.get('href', '')
                    
                    if title and href:
                        full_url = urljoin('https://www.zhihu.com', href)
                        results.append({
                            'title': title,
                            'url': full_url,
                            'excerpt': item.get_text(strip=True)[:300]
                        })
            
            return results[:10]
        except Exception as e:
            print(f"  Search failed: {e}")
            return []
    
    def scrape_page_content(self, url: str) -> Dict[str, Any]:
        """Extract content from article/answer page."""
        try:
            resp = self.get_with_retry(url)
            if not resp:
                return {'content': "", 'success': False}
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Remove scripts and styles
            for script in soup(['script', 'style']):
                script.decompose()
            
            content = ""
            
            # Try various content container selectors
            containers = [
                soup.find('div', class_=re.compile(r'RichText', re.I)),
                soup.find('div', class_=re.compile(r'answer-text|zm-editable', re.I)),
                soup.find('article'),
                soup.find('main'),
            ]
            
            for container in containers:
                if container:
                    content = container.get_text(separator=' ', strip=True)
                    if len(content) > 200:
                        break
            
            # Fallback to all text
            if not content or len(content) < 100:
                content = soup.get_text(separator=' ', strip=True)
            
            content = ' '.join(content.split())
            
            return {
                'content': content[:5000],
                'success': len(content) > 100
            }
        except Exception as e:
            return {'content': "", 'success': False, 'error': str(e)}
    
    def run_search(self, venue_id: str, search_query: str, max_posts: int = 5) -> List[Dict]:
        """Run a single search and extract key information."""
        print(f"  Searching: {search_query}")
        
        posts = []
        results = self.search_web(search_query)
        
        if not results:
            print(f"    No results found")
            return []
        
        print(f"    Found {len(results)} results")
        
        for i, result in enumerate(results[:max_posts]):
            if not result.get('url'):
                continue
            
            url = result['url']
            page_data = self.scrape_page_content(url)
            
            if page_data['success']:
                # Extract key information (simplified)
                full_text = result.get('excerpt', '') + ' ' + page_data.get('content', '')
                
                # Find pricing mentions
                pricing = re.findall(r'(\d+)[万千百]', full_text)
                
                # Find key phrases
                excerpts = full_text.split('。')[:3]
                
                posts.append({
                    'title': result.get('title', 'Untitled')[:200],
                    'url': url,
                    'key_excerpts': [e.strip() for e in excerpts if e.strip()][:5],
                    'pricing_mentions': list(set(pricing[:3])),
                    'experience_notes': [],
                    'warnings': []
                })
            
            time.sleep(1)  # Rate limiting
        
        return posts


def main():
    """Example usage with configuration options."""
    
    print("Zhihu Enhanced Scraper")
    print("=" * 50)
    print()
    print("CONFIGURATION OPTIONS:")
    print()
    print("1. Direct Access (requires valid session):")
    print("   ZHIHU_COOKIES=cookies.json python3 enhanced_zhihu_scraper.py")
    print()
    print("2. Proxy-Based Access:")
    print("   ZHIHU_PROXY=http://proxy:port python3 enhanced_zhihu_scraper.py")
    print()
    print("3. Browser-Based (Selenium):")
    print("   python3 enhanced_zhihu_scraper.py --selenium")
    print()
    print("=" * 50)
    print()
    
    # Check for proxy env var
    proxy = os.getenv('ZHIHU_PROXY')
    cookies_file = os.getenv('ZHIHU_COOKIES')
    
    if not proxy and not cookies_file:
        print("⚠️  No proxy or cookies configured.")
        print()
        print("To run this scraper successfully:")
        print()
        print("Option A: Export proxy environment variable")
        print("  export ZHIHU_PROXY='http://proxy-ip:port'")
        print()
        print("Option B: Create cookies.json with Zhihu session cookies")
        print("  {")
        print('    "z_c0": "your-cookie-value",')
        print('    "other_cookies": "value"')
        print("  }")
        print()
        return 1
    
    try:
        scraper = EnhancedZhihuScraper(
            "data/staging/zhihu",
            cookies_file=cookies_file,
            proxy=proxy
        )
        
        print(f"✓ Scraper initialized")
        print(f"  Proxy: {proxy if proxy else 'None'}")
        print(f"  Cookies: {cookies_file if cookies_file else 'None'}")
        print()
        
        # Test single search
        test_result = scraper.run_search(
            "test-venue",
            "巴厘岛婚礼",
            max_posts=1
        )
        
        if test_result:
            print(f"✓ Successfully scraped {len(test_result)} posts")
            return 0
        else:
            print("✗ No posts scraped - access still blocked")
            return 1
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
