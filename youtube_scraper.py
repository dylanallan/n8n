from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
from config import YOUTUBE_API_KEY, NUMBER_OF_CREATORS, VIDEOS_PER_CREATOR, ENGAGEMENT_THRESHOLD

class YouTubeScraper:
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        
    def get_top_creators(self, niche):
        """Get top creators in a specific niche"""
        try:
            search_response = self.youtube.search().list(
                q=niche,
                type='channel',
                part='snippet',
                maxResults=NUMBER_OF_CREATORS,
                order='viewCount'
            ).execute()
            
            creators = []
            for item in search_response['items']:
                channel_id = item['id']['channelId']
                channel_stats = self.youtube.channels().list(
                    id=channel_id,
                    part='statistics'
                ).execute()
                
                creators.append({
                    'channel_id': channel_id,
                    'title': item['snippet']['title'],
                    'subscriber_count': int(channel_stats['items'][0]['statistics']['subscriberCount']),
                    'view_count': int(channel_stats['items'][0]['statistics']['viewCount'])
                })
            
            return sorted(creators, key=lambda x: x['subscriber_count'], reverse=True)
            
        except HttpError as e:
            print(f'An error occurred: {e}')
            return []

    def get_top_videos(self, channel_id):
        """Get top performing videos from a channel"""
        try:
            search_response = self.youtube.search().list(
                channelId=channel_id,
                type='video',
                part='snippet',
                maxResults=VIDEOS_PER_CREATOR,
                order='viewCount'
            ).execute()
            
            videos = []
            for item in search_response['items']:
                video_id = item['id']['videoId']
                video_stats = self.youtube.videos().list(
                    id=video_id,
                    part='statistics,snippet'
                ).execute()
                
                stats = video_stats['items'][0]['statistics']
                snippet = video_stats['items'][0]['snippet']
                
                engagement = int(stats.get('likeCount', 0)) + int(stats.get('commentCount', 0))
                
                if engagement >= ENGAGEMENT_THRESHOLD:
                    videos.append({
                        'video_id': video_id,
                        'title': snippet['title'],
                        'description': snippet['description'],
                        'published_at': snippet['publishedAt'],
                        'view_count': int(stats.get('viewCount', 0)),
                        'like_count': int(stats.get('likeCount', 0)),
                        'comment_count': int(stats.get('commentCount', 0)),
                        'engagement_rate': engagement / int(stats.get('viewCount', 1))
                    })
            
            return videos
            
        except HttpError as e:
            print(f'An error occurred: {e}')
            return []

    def analyze_content(self, videos):
        """Analyze video content for hooks, titles, and other metrics"""
        analysis = []
        for video in videos:
            # Basic content analysis
            hook_analysis = self._analyze_hook(video['title'], video['description'])
            title_analysis = self._analyze_title(video['title'])
            
            analysis.append({
                'video_id': video['video_id'],
                'title': video['title'],
                'hook_analysis': hook_analysis,
                'title_analysis': title_analysis,
                'engagement_metrics': {
                    'views': video['view_count'],
                    'likes': video['like_count'],
                    'comments': video['comment_count'],
                    'engagement_rate': video['engagement_rate']
                }
            })
        
        return analysis

    def _analyze_hook(self, title, description):
        """Analyze video hook patterns"""
        # Basic hook analysis - can be expanded with more sophisticated NLP
        hook_patterns = {
            'question': '?' in title,
            'number': any(char.isdigit() for char in title),
            'emotional': any(word in title.lower() for word in ['amazing', 'incredible', 'unbelievable']),
            'how_to': title.lower().startswith('how to'),
            'why': title.lower().startswith('why')
        }
        return hook_patterns

    def _analyze_title(self, title):
        """Analyze title patterns"""
        # Basic title analysis - can be expanded with more sophisticated NLP
        title_patterns = {
            'length': len(title),
            'has_emoji': any(ord(c) > 127 for c in title),
            'has_caps': any(c.isupper() for c in title),
            'word_count': len(title.split())
        }
        return title_patterns

    def save_to_spreadsheet(self, data, filename):
        """Save analysis data to spreadsheet"""
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False) 