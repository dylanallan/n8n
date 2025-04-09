import instaloader
from datetime import datetime, timedelta
import pandas as pd
from config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, NUMBER_OF_CREATORS, VIDEOS_PER_CREATOR, ENGAGEMENT_THRESHOLD

class InstagramScraper:
    def __init__(self):
        self.L = instaloader.Instaloader()
        self.L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        
    def get_top_creators(self, niche):
        """Get top creators in a specific niche"""
        try:
            # Search for hashtags related to the niche
            hashtag = self.L.get_hashtag_posts(niche)
            creators = {}
            
            for post in hashtag:
                if len(creators) >= NUMBER_OF_CREATORS:
                    break
                    
                profile = post.owner_profile
                if profile.username not in creators:
                    creators[profile.username] = {
                        'username': profile.username,
                        'followers': profile.followers,
                        'posts': profile.mediacount,
                        'engagement_rate': self._calculate_engagement_rate(profile)
                    }
            
            return sorted(creators.values(), key=lambda x: x['followers'], reverse=True)
            
        except Exception as e:
            print(f'An error occurred: {e}')
            return []

    def get_top_posts(self, username):
        """Get top performing posts from a creator"""
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)
            posts = []
            
            for post in profile.get_posts():
                if len(posts) >= VIDEOS_PER_CREATOR:
                    break
                    
                engagement = post.likes + post.comments
                if engagement >= ENGAGEMENT_THRESHOLD:
                    posts.append({
                        'post_id': post.shortcode,
                        'caption': post.caption,
                        'likes': post.likes,
                        'comments': post.comments,
                        'timestamp': post.date,
                        'engagement_rate': engagement / profile.followers if profile.followers > 0 else 0
                    })
            
            return posts
            
        except Exception as e:
            print(f'An error occurred: {e}')
            return []

    def analyze_content(self, posts):
        """Analyze post content for hooks, captions, and other metrics"""
        analysis = []
        for post in posts:
            hook_analysis = self._analyze_hook(post['caption'])
            caption_analysis = self._analyze_caption(post['caption'])
            
            analysis.append({
                'post_id': post['post_id'],
                'caption': post['caption'],
                'hook_analysis': hook_analysis,
                'caption_analysis': caption_analysis,
                'engagement_metrics': {
                    'likes': post['likes'],
                    'comments': post['comments'],
                    'engagement_rate': post['engagement_rate']
                }
            })
        
        return analysis

    def _analyze_hook(self, caption):
        """Analyze post hook patterns"""
        if not caption:
            return {}
            
        hook_patterns = {
            'question': '?' in caption,
            'number': any(char.isdigit() for char in caption),
            'emotional': any(word in caption.lower() for word in ['amazing', 'incredible', 'unbelievable']),
            'call_to_action': any(word in caption.lower() for word in ['check out', 'click', 'link in bio']),
            'hashtag_count': caption.count('#')
        }
        return hook_patterns

    def _analyze_caption(self, caption):
        """Analyze caption patterns"""
        if not caption:
            return {}
            
        caption_patterns = {
            'length': len(caption),
            'has_emoji': any(ord(c) > 127 for c in caption),
            'has_caps': any(c.isupper() for c in caption),
            'word_count': len(caption.split()),
            'line_count': caption.count('\n') + 1
        }
        return caption_patterns

    def _calculate_engagement_rate(self, profile):
        """Calculate average engagement rate for a profile"""
        try:
            total_engagement = 0
            post_count = 0
            
            for post in profile.get_posts():
                if post_count >= 10:  # Look at last 10 posts
                    break
                total_engagement += post.likes + post.comments
                post_count += 1
                
            return total_engagement / (post_count * profile.followers) if post_count > 0 and profile.followers > 0 else 0
            
        except Exception as e:
            print(f'Error calculating engagement rate: {e}')
            return 0

    def save_to_spreadsheet(self, data, filename):
        """Save analysis data to spreadsheet"""
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False) 