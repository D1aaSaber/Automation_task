import requests
import logging

class DataProvider:
    def __init__(self, api_url=None):
        self.api_url = api_url if api_url else "https://jsonplaceholder.typicode.com/posts"
        self.logger = logging.getLogger(__name__)
    def fetch_posts(self, limit=3):
        try:
            self.logger.info(f"Fetching data from {self.api_url}...")
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            posts = response.json()[:limit]
            self.logger.info(f"Successfully fetched {len(posts)} posts")
            return posts
        except Exception as e:
            self.logger.error(f"API Fetch Error: {e}")
            return []