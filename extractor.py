import praw
import sqlite3
import json
import re
import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class StartupCommentAnalyzer:
    def __init__(self):
        # Initialize Reddit API
        self.reddit = praw.Reddit(
            client_id='YOUR_CLIENT_ID',
            client_secret='YOUR_CLIENT_SECRET',
            user_agent='startup_scraper_v1'
        )
        
        # Ollama configuration
        self.ollama_url = "http://localhost:11434/api/generate"
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        self.conn = sqlite3.connect('startups.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS startups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                startup_name TEXT,
                location TEXT,
                company_url TEXT,
                description TEXT,
                comment_text TEXT,
                comment_id TEXT UNIQUE,
                subreddit TEXT,
                created_utc TIMESTAMP
            )
        ''')
        self.conn.commit()
        logger.info("Database initialized successfully")

    def extract_with_ollama(self, comment_text: str) -> List[Dict]:
        clean_text = self.clean_comment_text(comment_text)
        prompt = self.create_extraction_prompt(clean_text)
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "llama2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "num_predict": 1024
                    }
                },
                timeout=120
            )
            if response.status_code == 200:
                result = response.json()
                return self.parse_llm_response(result["response"])
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Ollama extraction failed: {e}")
            return []

    def create_extraction_prompt(self, comment_text: str) -> str:
        return f"""You are an advanced data extraction model.
Analyze unstructured Reddit comments about startups and extract structured data.
Return ONLY valid JSON array:

[
  {{
    "startup_name": "",
    "location": "",
    "company_url": "",
    "description": ""
  }}
]

Comment:
{comment_text}
"""
    def clean_comment_text(self, text: str) -> str:
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def parse_llm_response(self, response: str) -> List[Dict]:
        try:
            json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                validated_data = []
                for item in data:
                    if isinstance(item, dict):
                        validated_data.append({
                            "startup_name": item.get("startup_name", ""),
                            "location": item.get("location", ""),
                            "company_url": item.get("company_url", ""),
                            "description": item.get("description", "")
                        })
                return validated_data
            return []
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            return []

    def is_startup_related(self, comment_text: str) -> bool:
        keywords = ['startup', 'company', 'founder', 'launch', 'product', 'app', 
                    'platform', 'saas', 'tech', 'venture', 'funding', 'seed', 
                    'round', 'investor', 'yc', 'accelerator', 'built', 'created',
                    'founded', 'business', 'entrepreneur']
        text_lower = comment_text.lower()
        return any(k in text_lower for k in keywords)

    def scrape_startup_comments(self, post_url: str, limit_comments: int = 30):
        try:
            submission = self.reddit.submission(url=post_url)
            submission.comments.replace_more(limit=0)
            
            comments_processed = 0
            startups_found = 0
            
            for comment in submission.comments.list()[:limit_comments]:
                if not comment.body or comment.body == '[deleted]' or len(comment.body.strip()) < 25:
                    continue
                if not self.is_startup_related(comment.body):
                    continue
                
                startups = self.extract_with_ollama(comment.body)
                
                for startup_info in startups:
                    if startup_info['startup_name'] or startup_info['company_url'] or startup_info['description']:
                        self.save_to_database(
                            startup_name=startup_info['startup_name'],
                            location=startup_info['location'],
                            company_url=startup_info['company_url'],
                            description=startup_info['description'],
                            comment_text=comment.body[:800],
                            comment_id=f"{comment.id}_{startups_found}",
                            subreddit=comment.subreddit.display_name,
                            created_utc=comment.created_utc
                        )
                        startups_found += 1
                
                comments_processed += 1
                
        except Exception as e:
            logger.error(f"Error: {str(e)}")

    def save_to_database(self, startup_name: str, location: str, company_url: str, 
                        description: str, comment_text: str, comment_id: str, 
                        subreddit: str, created_utc: float):
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO startups 
                (startup_name, location, company_url, description, comment_text, comment_id, subreddit, created_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (startup_name, location, company_url, description, comment_text, comment_id, subreddit, created_utc))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Database error: {e}")

    def query_startups(self, query: str = "SELECT * FROM startups"):
        try:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Query error: {e}")
            return []

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()
        logger.info("Database connection closed")
