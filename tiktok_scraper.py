from TikTokApi import TikTokApi
import pandas as pd
from config import TIKTOK_SESSION_ID, NUMBER_OF_CREATORS, VIDEOS_PER_CREATOR, ENGAGEMENT_THRESHOLD

class TikTokScraper:
    def __init__(self):
        self.api = TikTokApi.get_instance()
        self.api._get_session_id = lambda: TIKTOK_SESSION_ID
        
    def get_top_creators(self, niche):
        """Get top creators in a specific niche"""
        try:
            hashtag = self.api.hashtag(niche)
            creators = {}
            
            for video in hashtag.videos(count=NUMBER_OF_CREATORS * 2):  # Get more to filter
                author = video.author
                if author.unique_id not in creators:
                    creators[author.unique_id] = {
                        'username': author.unique_id,
                        'followers': author.stats['followerCount'],
                        'videos': author.stats['videoCount'],
                        'engagement_rate': self._calculate_engagement_rate(author)
                    }
                    
                if len(creators) >= NUMBER_OF_CREATORS:
                    break
            
            return sorted(creators.values(), key=lambda x: x['followers'], reverse=True)
            
        except Exception as e:
            print(f'An error occurred: {e}')
            return []

    def get_top_videos(self, username):
        """Get top performing videos from a creator"""
        try:
            user = self.api.user(username)
            videos = []
            
            for video in user.videos(count=VIDEOS_PER_CREATOR * 2):  # Get more to filter
                engagement = video.stats['diggCount'] + video.stats['commentCount']
                if engagement >= ENGAGEMENT_THRESHOLD:
                    videos.append({
                        'video_id': video.id,
                        'description': video.desc,
                        'likes': video.stats['diggCount'],
                        'comments': video.stats['commentCount'],
                        'shares': video.stats['shareCount'],
                        'timestamp': video.create_time,
                        'engagement_rate': engagement / video.stats['playCount'] if video.stats['playCount'] > 0 else 0
                    })
                
                if len(videos) >= VIDEOS_PER_CREATOR:
                    break
            
            return videos
            
        except Exception as e:
            print(f'An error occurred: {e}')
            return []

    def analyze_content(self, videos):
        """Analyze video content for hooks, descriptions, and other metrics"""
        analysis = []
        for video in videos:
            hook_analysis = self._analyze_hook(video['description'])
            description_analysis = self._analyze_description(video['description'])
            
            analysis.append({
                'video_id': video['video_id'],
                'description': video['description'],
                'hook_analysis': hook_analysis,
                'description_analysis': description_analysis,
                'engagement_metrics': {
                    'likes': video['likes'],
                    'comments': video['comments'],
                    'shares': video['shares'],
                    'engagement_rate': video['engagement_rate']
                }
            })
        
        return analysis

    def _analyze_hook(self, description):
        """Analyze video hook patterns"""
        if not description:
            return {}
            
        hook_patterns = {
            'question': '?' in description,
            'number': any(char.isdigit() for char in description),
            'emotional': any(word in description.lower() for word in ['amazing', 'incredible', 'unbelievable']),
            'trending': any(word in description.lower() for word in ['trending', 'viral', 'fyp']),
            'hashtag_count': description.count('#')
        }
        return hook_patterns

    def _analyze_description(self, description):
        """Analyze description patterns"""
        if not description:
            return {}
            
        description_patterns = {
            'length': len(description),
            'has_emoji': any(ord(c) > 127 for c in description),
            'has_caps': any(c.isupper() for c in description),
            'word_count': len(description.split()),
            'hashtag_count': description.count('#')
        }
        return description_patterns

    def _calculate_engagement_rate(self, author):
        """Calculate average engagement rate for a creator"""
        try:
            total_engagement = 0
            video_count = 0
            
            for video in author.videos(count=10):  # Look at last 10 videos
                total_engagement += video.stats['diggCount'] + video.stats['commentCount']
                video_count += 1
                
            return total_engagement / (video_count * author.stats['followerCount']) if video_count > 0 and author.stats['followerCount'] > 0 else 0
            
        except Exception as e:
            print(f'Error calculating engagement rate: {e}')
            return 0

    def save_to_spreadsheet(self, data, filename):
        """Save analysis data to spreadsheet"""
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False) 