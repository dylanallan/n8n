import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
TIKTOK_SESSION_ID = os.getenv('TIKTOK_SESSION_ID')

# Scraping Configuration
NUMBER_OF_CREATORS = 20
VIDEOS_PER_CREATOR = 10
ENGAGEMENT_THRESHOLD = 1000  # Minimum engagement count to consider a video

# Output Configuration
OUTPUT_DIR = 'output'
SPREADSHEET_NAME = 'viral_content_analysis.xlsx'

# Platform-specific settings
PLATFORMS = ['youtube', 'instagram', 'tiktok']

# Analysis categories
ANALYSIS_CATEGORIES = [
    'hook_analysis',
    'title_analysis',
    'visual_analysis',
    'subject_analysis',
    'engagement_metrics'
] 