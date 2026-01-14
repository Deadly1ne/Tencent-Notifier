# Tencent Animation Notifier

A GitHub Actions workflow and Python script to monitor manga chapters on `ac.qq.com` and send Discord notifications.

## Features
- **Scraper**: Scrapes Tencent Animation SSR pages using BeautifulSoup.
- **State Management**: Tracks known chapters to only notify about new ones.
- **Discord Integration**: Sends rich embed notifications with chapter details.
- **GitHub Actions**: Runs automatically every 30 minutes.

## Setup

1. **Fork/Clone this repository.**
2. **Configure Series**:
   Edit `config.json` to add the series you want to track.
   ```json
   {
       "series": [
           {
               "url": "https://ac.qq.com/Comic/comicInfo/id/657037",
               "alias": "My Favorite Manga"
           }
       ],
       "webhook_url": "YOUR_DISCORD_WEBHOOK_URL"
   }
   ```

3. **Enable GitHub Actions**:
   Go to the "Actions" tab in your repository and ensure workflows are enabled.
   The workflow needs write permissions to the repository to update `state.json`. 
   Go to `Settings -> Actions -> General -> Workflow permissions` and select "Read and write permissions".

## Local Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the script:
   ```bash
   python main.py
   ```
