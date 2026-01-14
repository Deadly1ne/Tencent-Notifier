import json
import os
import logging
import requests
import time
from datetime import datetime, timezone
from scraper import TencentScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONFIG_FILE = 'config.json'
STATE_FILE = 'state.json'

class DiscordNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_notification(self, series_alias, chapter, series_info=None):
        """
        Sends a Discord notification for a new chapter.
        """
        # Default footer if info is missing
        footer_text = f"Chapter ID: {chapter['id']} | Date: {chapter['created_at']}"
        thumbnail_url = ""
        
        if series_info:
            series_id = series_info.get('id', 'Unknown')
            date_str = str(chapter['created_at']).replace('-', '.')
            footer_text = f"Series ID: {series_id} | Chapter ID: {chapter['id']} | Date: {date_str}"
            thumbnail_url = series_info.get('cover_image_url', "")

        embed = {
            "title": f"New Chapter of {series_alias}",
            "description": f"**{chapter['title']}**",
            "url": chapter['url'],
            "color": 16750848,  # Tencent Orange? (FF7F00) -> 16744192. Let's use generic orange.
            "thumbnail": {
                "url": thumbnail_url
            },
            "footer": {
                "text": footer_text
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            response = requests.post(self.webhook_url, json=payload)
            if response.status_code == 429:
                retry_after = float(response.headers.get('Retry-After', 1))
                logger.warning(f"Rate limited. Sleeping for {retry_after}s")
                time.sleep(retry_after)
                # Retry once
                response = requests.post(self.webhook_url, json=payload)
            
            response.raise_for_status()
            logger.info(f"Notification sent for {series_alias} - {chapter['title']}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

class StateManager:
    def __init__(self, filepath):
        self.filepath = filepath
        self.state = self.load_state()

    def load_state(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                return {}
        return {}

    def save_state(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def get_series_state(self, url):
        return self.state.get(url, {"last_chapter_number": -1.0})

    def update_series_state(self, url, last_chapter_number):
        self.state[url] = {"last_chapter_number": last_chapter_number}

def main():
    # Load config
    if not os.path.exists(CONFIG_FILE):
        logger.error(f"Config file {CONFIG_FILE} not found.")
        return

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)

    webhook_url = config.get('webhook_url')
    if not webhook_url:
        logger.error("No webhook_url in config.")
        return

    notifier = DiscordNotifier(webhook_url)
    state_manager = StateManager(STATE_FILE)
    scraper = TencentScraper()

    for series in config.get('series', []):
        url = series['url']
        alias = series.get('alias', 'Unknown Series')
        
        logger.info(f"Checking {alias} ({url})...")
        
        result = scraper.fetch_chapters(url)
        current_chapters = result.get('chapters', [])
        series_info = result.get('series_info', {})
        
        if not current_chapters:
            logger.warning(f"No chapters found for {alias}.")
            continue

        series_state = state_manager.get_series_state(url)
        last_number = series_state.get('last_chapter_number', -1.0)
        
        # Identify new chapters
        new_chapters = []
        max_number = last_number
        
        for ch in current_chapters:
            if ch['number'] > last_number:
                new_chapters.append(ch)
            
            if ch['number'] > max_number:
                max_number = ch['number']
        
        # If this is the first run (last_number is -1.0), do not notify all, just populate state
        if last_number == -1.0:
            logger.info(f"First run for {alias}. Initializing state with last chapter {max_number}.")
            state_manager.update_series_state(url, max_number)
            continue
            
        if new_chapters:
            logger.info(f"Found {len(new_chapters)} new chapters for {alias}.")
            # Sort new chapters by number to send notifications in order
            new_chapters.sort(key=lambda x: x['number'])
            
            for ch in new_chapters:
                notifier.send_notification(alias, ch, series_info)
                time.sleep(1) # Rate limit protection
                
        else:
            logger.info(f"No new chapters for {alias}.")

        # Update state with the highest number found
        if max_number > last_number:
            state_manager.update_series_state(url, max_number)
        
        # Rate limiting
        time.sleep(2)

    state_manager.save_state()

if __name__ == "__main__":
    main()
