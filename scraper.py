import requests
from bs4 import BeautifulSoup
import re
import logging
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TencentScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Upgrade-Insecure-Requests": "1",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Mount retry adapter
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def fetch_chapters(self, topic_url):
        try:
            logger.info(f"Fetching {topic_url}...")
            
            # Try to fetch
            response = self.session.get(topic_url, timeout=20)
            response.raise_for_status()
            
            # Check if we got valid HTML or some verification page
            if "ac.qq.com" not in response.text and "腾讯动漫" not in response.text:
                # Basic check
                pass

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Series Info
            series_info = {}
            
            # Title
            title_tag = soup.select_one('.works-intro-title strong')
            if title_tag:
                series_info['title'] = title_tag.get_text(strip=True)
            
            # Cover
            cover_tag = soup.select_one('.works-cover img')
            if cover_tag:
                series_info['cover_image_url'] = cover_tag.get('src')
                
            # ID (from URL)
            match = re.search(r'id/(\d+)', topic_url)
            if match:
                series_info['id'] = match.group(1)
            else:
                series_info['id'] = 'unknown'

            # Chapters
            chapters = []
            chapter_list = soup.select('.chapter-page-all .works-chapter-item')
            
            for item in chapter_list:
                link_tag = item.select_one('a')
                if not link_tag:
                    continue
                
                href = link_tag.get('href')
                full_title = link_tag.get('title', '').strip()
                display_title = link_tag.get_text(strip=True)
                
                c_title = display_title if display_title else full_title
                
                # Extract CID
                cid_match = re.search(r'cid/(\d+)', href)
                c_id = cid_match.group(1) if cid_match else '0'
                
                # Check locked status
                is_locked = bool(item.select_one('.ui-icon-pay'))
                
                # Extract number
                c_number = -1.0
                num_match = re.search(r'(?:第)?(\d+(\.\d+)?)', c_title)
                if num_match:
                    try:
                        c_number = float(num_match.group(1))
                    except:
                        pass
                
                chapters.append({
                    'id': c_id,
                    'title': c_title,
                    'url': f"https://ac.qq.com{href}",
                    'created_at': datetime.now().strftime('%Y-%m-%d'), # Use current date as fallback
                    'locked': is_locked,
                    'number': c_number
                })
            
            return {'chapters': chapters, 'series_info': series_info}

        except Exception as e:
            logger.error(f"Error fetching {topic_url}: {e}")
            return {'chapters': [], 'series_info': {}}

from datetime import datetime
if __name__ == "__main__":
    scraper = TencentScraper()
    res = scraper.fetch_chapters("https://ac.qq.com/Comic/comicInfo/id/657037")
    print(f"Found {len(res['chapters'])} chapters")
    if res['chapters']:
        print("First:", res['chapters'][0])
        print("Last:", res['chapters'][-1])
