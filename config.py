import os
from dotenv import load_dotenv

class Config:
    """Centralized configuration management"""
    
    def __init__(self, env_path='.env'):
        load_dotenv(env_path)
        self._load_database_config()
        self._load_api_config()
        self._load_scraper_config()
    
    def _load_database_config(self):
        """Load database configuration"""
        self.db_name = os.getenv('DB_NAME')
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', 5432)
    
    def _load_api_config(self):
        """Load API configuration"""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    def _load_scraper_config(self):
        """Load scraper configuration"""
        self.base_url = "https://www.gsmarena.com/"
        self.samsung_url = "https://www.gsmarena.com/samsung-phones-9.php"
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.request_delay = 5  # seconds between requests
    
    def get_db_params(self):
        """Get database connection parameters"""
        return {
            'dbname': self.db_name,
            'user': self.db_user,
            'password': self.db_password,
            'host': self.db_host,
            'port': self.db_port
        }