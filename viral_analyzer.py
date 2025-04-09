import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.cluster import KMeans
import joblib
import os
from datetime import datetime, timedelta
from textblob import TextBlob
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
from collections import Counter
import requests
import json

class ViralContentAnalyzer:
    def __init__(self):
        self.model_path = 'models/viral_predictor.joblib'
        self.vectorizer_path = 'models/tfidf_vectorizer.joblib'
        self.scaler_path = 'models/feature_scaler.joblib'
        self.model = None
        self.vectorizer = None
        self.scaler = None
        self.sia = SentimentIntensityAnalyzer()
        self._load_models()
        self._download_nltk_data()
        
        # Dylltoamill content frameworks
        self.hook_types = {
            'storytelling': ['Once upon a time', 'Let me tell you about', 'I never expected'],
            'shock': ['You won\'t believe', 'I was shocked when', 'This changed everything'],
            'authority': ['As a [expert]', 'After [experience]', 'Based on my research'],
            'relatability': ['Ever feel like', 'We\'ve all been there', 'Can you relate?'],
            'curiosity': ['What if I told you', 'The secret to', 'Here\'s why'],
            'urgency': ['Before it\'s too late', 'Limited time', 'Don\'t miss out'],
            'social_proof': ['Everyone is talking about', 'Join thousands of', 'The trend you need to know'],
            'problem_solution': ['Struggling with', 'Tired of', 'The solution to'],
            'transformation': ['From [before] to [after]', 'How I went from', 'The journey to'],
            'exclusive': ['Insider secret', 'Behind the scenes', 'What they don\'t want you to know']
        }
        
        self.storytelling_angles = {
            'personal_journey': 'Share your transformation story',
            'behind_scenes': 'Show the process and work',
            'expert_tips': 'Share professional insights',
            'community_stories': 'Highlight audience success',
            'trend_analysis': 'Break down current trends',
            'problem_solution': 'Address common pain points',
            'comparison': 'Before vs after scenarios',
            'tutorial': 'Step-by-step guides',
            'reaction': 'Share opinions on trends',
            'collaboration': 'Feature other creators'
        }
        
        self.cta_formats = {
            'question': 'What do you think? Comment below!',
            'share': 'Tag someone who needs to see this!',
            'save': 'Save this for later!',
            'follow': 'Follow for more [value]',
            'link': 'Link in bio for [offer]',
            'challenge': 'Try this and tag me!',
            'poll': 'Which one would you choose?',
            'story': 'DM me your story!',
            'join': 'Join our community!',
            'learn': 'Want to learn more?'
        }

        # Platform-specific feature tracking
        self.platform_features = {
            'youtube': {
                'shorts': self._track_youtube_shorts_trends,
                'community': self._track_youtube_community_trends,
                'playlists': self._track_youtube_playlist_trends,
                'live': self._track_youtube_live_trends
            },
            'instagram': {
                'reels': self._track_instagram_reels_trends,
                'stories': self._track_instagram_stories_trends,
                'guides': self._track_instagram_guides_trends,
                'live': self._track_instagram_live_trends
            },
            'tiktok': {
                'sounds': self._track_tiktok_sound_trends,
                'effects': self._track_tiktok_effect_trends,
                'series': self._track_tiktok_series_trends,
                'live': self._track_tiktok_live_trends
            }
        }
        
        # Cache for trending data
        self.trending_cache = {}
        self.cache_expiry = timedelta(hours=1)

    def _download_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('sentiment/vader_lexicon')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('vader_lexicon')

    def _load_models(self):
        """Load or initialize ML models"""
        os.makedirs('models', exist_ok=True)
        
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.vectorizer = joblib.load(self.vectorizer_path)
            self.scaler = joblib.load(self.scaler_path)
        else:
            self.model = GradientBoostingClassifier(n_estimators=200, learning_rate=0.1, random_state=42)
            self.vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 3))
            self.scaler = StandardScaler()

    def _extract_features(self, content_data):
        """Extract advanced features from content data"""
        features = []
        
        for item in content_data:
            # Text features
            text = item.get('title', '') + ' ' + item.get('description', '')
            
            # Sentiment analysis
            sentiment = self.sia.polarity_scores(text)
            
            # Text complexity
            tokens = word_tokenize(text.lower())
            words = [word for word in tokens if word.isalpha()]
            unique_words = len(set(words))
            avg_word_length = np.mean([len(word) for word in words]) if words else 0
            
            # Engagement velocity
            engagement = item.get('engagement_metrics', {})
            views = engagement.get('views', 0)
            likes = engagement.get('likes', 0)
            comments = engagement.get('comments', 0)
            shares = engagement.get('shares', 0)
            
            # Calculate engagement ratios
            like_ratio = likes / views if views > 0 else 0
            comment_ratio = comments / views if views > 0 else 0
            share_ratio = shares / views if views > 0 else 0
            
            # Time-based features
            timestamp = item.get('timestamp', datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            hour = timestamp.hour
            day_of_week = timestamp.weekday()
            
            # Hook features
            hook_analysis = item.get('hook_analysis', {})
            hook_features = [
                int(hook_analysis.get('question', False)),
                int(hook_analysis.get('number', False)),
                int(hook_analysis.get('emotional', False)),
                int(hook_analysis.get('trending', False))
            ]
            
            # Combine all features
            feature_vector = np.concatenate([
                self.vectorizer.transform([text]).toarray()[0],
                [sentiment['pos'], sentiment['neg'], sentiment['neu'], sentiment['compound']],
                [unique_words, avg_word_length],
                [views, likes, comments, shares],
                [like_ratio, comment_ratio, share_ratio],
                [hour, day_of_week],
                hook_features
            ])
            
            features.append(feature_vector)
        
        return np.array(features)

    def train_model(self, historical_data):
        """Train the viral content prediction model with cross-validation"""
        X = self._extract_features(historical_data)
        y = [1 if item.get('engagement_metrics', {}).get('views', 0) > 100000 else 0 
             for item in historical_data]
        
        # Split data for validation
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate model
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        
        print(f"Model Performance:")
        print(f"Accuracy: {accuracy:.2%}")
        print(f"Precision: {precision:.2%}")
        print(f"Recall: {recall:.2%}")
        
        # Save models
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        joblib.dump(self.scaler, self.scaler_path)

    def predict_virality(self, content_data):
        """Predict virality probability for content with confidence scores"""
        X = self._extract_features(content_data)
        X_scaled = self.scaler.transform(X)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        return probabilities

    def generate_optimization_recommendations(self, content_data, virality_scores):
        """Generate detailed optimization recommendations"""
        recommendations = []
        
        for i, (content, score) in enumerate(zip(content_data, virality_scores)):
            rec = {
                'content_id': content.get('video_id') or content.get('post_id'),
                'virality_score': score,
                'recommendations': [],
                'confidence_score': self._calculate_confidence_score(content, score)
            }
            
            # Analyze hooks
            hook_analysis = content.get('hook_analysis', {})
            if not hook_analysis.get('question'):
                rec['recommendations'].append({
                    'type': 'hook',
                    'priority': 'high',
                    'message': "Add a question hook to increase engagement",
                    'example': "Did you know...? What if...?"
                })
            if not hook_analysis.get('emotional'):
                rec['recommendations'].append({
                    'type': 'hook',
                    'priority': 'medium',
                    'message': "Incorporate emotional triggers in the content",
                    'example': "You won't believe what happened next..."
                })
            
            # Analyze engagement metrics
            engagement = content.get('engagement_metrics', {})
            if engagement.get('comments', 0) < engagement.get('likes', 0) * 0.1:
                rec['recommendations'].append({
                    'type': 'engagement',
                    'priority': 'high',
                    'message': "Add call-to-action for comments",
                    'example': "What do you think? Comment below!"
                })
            
            # Content optimization
            text = content.get('title', '') + ' ' + content.get('description', '')
            sentiment = self.sia.polarity_scores(text)
            
            if sentiment['compound'] < -0.5:
                rec['recommendations'].append({
                    'type': 'sentiment',
                    'priority': 'high',
                    'message': "Content is too negative, consider balancing with positive elements",
                    'example': "Add positive outcomes or solutions"
                })
            
            # Time optimization
            timestamp = content.get('timestamp', datetime.now())
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            if timestamp.hour not in [10, 14, 19]:  # Peak engagement hours
                rec['recommendations'].append({
                    'type': 'timing',
                    'priority': 'medium',
                    'message': f"Consider posting during peak hours (10 AM, 2 PM, or 7 PM)",
                    'example': "Schedule content for optimal engagement times"
                })
            
            recommendations.append(rec)
        
        return recommendations

    def _calculate_confidence_score(self, content, virality_score):
        """Calculate confidence score for predictions"""
        # Consider multiple factors for confidence
        engagement = content.get('engagement_metrics', {})
        views = engagement.get('views', 0)
        likes = engagement.get('likes', 0)
        
        # Base confidence on data quality
        data_quality = min(1.0, views / 10000)  # Normalize to 0-1
        
        # Adjust confidence based on engagement patterns
        engagement_pattern = likes / views if views > 0 else 0
        engagement_quality = min(1.0, engagement_pattern * 10)  # Normalize to 0-1
        
        # Combine factors
        confidence = (data_quality * 0.4 + engagement_quality * 0.3 + virality_score * 0.3)
        return confidence

    def get_trending_topics(self, platform, niche):
        """Get currently trending topics with advanced analysis"""
        features = self.get_platform_features(platform)
        
        # Combine platform-specific trends with niche-specific analysis
        trending_data = {
            'hashtags': self._analyze_hashtag_trends(platform, niche),
            'topics': self._analyze_topic_trends(platform, niche),
            'keywords': self._analyze_keyword_trends(platform, niche),
            'platform_features': features
        }
        
        return trending_data

    def _track_youtube_shorts_trends(self):
        """Track trending YouTube Shorts features"""
        # This would be implemented with YouTube API
        return {
            'top_effects': ['Green Screen', 'Text Overlay', 'Transitions'],
            'top_music': ['Trending Song 1', 'Trending Song 2'],
            'top_topics': ['Quick Tips', 'Behind the Scenes', 'Challenges'],
            'engagement_patterns': {
                'average_watch_time': '0:45',
                'best_post_times': ['10:00', '14:00', '18:00'],
                'optimal_length': '0:30-0:45'
            }
        }
    
    def _track_youtube_community_trends(self):
        """Track YouTube Community tab trends"""
        return {
            'top_post_types': ['Polls', 'Images', 'Text Updates'],
            'engagement_patterns': {
                'best_post_frequency': '2-3 times per week',
                'optimal_post_length': '100-200 characters',
                'best_media_types': ['Images', 'Polls']
            }
        }
    
    def _track_youtube_playlist_trends(self):
        """Track YouTube playlist trends"""
        return {
            'top_playlist_types': ['Tutorial Series', 'Compilations', 'Themed Collections'],
            'optimal_videos_per_playlist': '5-10',
            'best_playlist_topics': ['How-to Guides', 'Product Reviews', 'Behind the Scenes']
        }
    
    def _track_youtube_live_trends(self):
        """Track YouTube Live trends"""
        return {
            'top_live_formats': ['Q&A', 'Tutorial', 'Behind the Scenes'],
            'optimal_duration': '30-60 minutes',
            'best_streaming_times': ['Evening', 'Weekend'],
            'engagement_tools': ['Super Chat', 'Polls', 'Live Chat']
        }
    
    def _track_instagram_reels_trends(self):
        """Track Instagram Reels trends"""
        return {
            'top_effects': ['Trending Effect 1', 'Trending Effect 2'],
            'top_music': ['Trending Song 1', 'Trending Song 2'],
            'top_topics': ['Quick Tips', 'Tutorials', 'Challenges'],
            'engagement_patterns': {
                'optimal_length': '15-30 seconds',
                'best_post_times': ['Morning', 'Evening'],
                'top_hashtags': ['#reels', '#reelsinstagram']
            }
        }
    
    def _track_instagram_stories_trends(self):
        """Track Instagram Stories trends"""
        return {
            'top_sticker_types': ['Polls', 'Questions', 'Countdown'],
            'optimal_story_count': '3-5 per day',
            'best_content_types': ['Behind the Scenes', 'Quick Tips', 'Polls'],
            'engagement_tools': ['Swipe Up', 'Polls', 'Questions']
        }
    
    def _track_instagram_guides_trends(self):
        """Track Instagram Guides trends"""
        return {
            'top_guide_types': ['Product Reviews', 'Tutorials', 'Resources'],
            'optimal_posts_per_guide': '5-10',
            'best_guide_topics': ['How-to Guides', 'Product Collections', 'Tutorials']
        }
    
    def _track_instagram_live_trends(self):
        """Track Instagram Live trends"""
        return {
            'top_live_formats': ['Q&A', 'Tutorial', 'Behind the Scenes'],
            'optimal_duration': '20-30 minutes',
            'best_streaming_times': ['Evening', 'Weekend'],
            'engagement_tools': ['Questions', 'Polls', 'Comments']
        }
    
    def _track_tiktok_sound_trends(self):
        """Track TikTok sound trends"""
        return {
            'top_sounds': ['Trending Sound 1', 'Trending Sound 2'],
            'sound_categories': ['Music', 'Voiceover', 'Original'],
            'usage_patterns': {
                'average_use_count': 10000,
                'trend_duration': '3-7 days',
                'best_use_times': ['Early Trend', 'Peak Trend']
            }
        }
    
    def _track_tiktok_effect_trends(self):
        """Track TikTok effect trends"""
        return {
            'top_effects': ['Trending Effect 1', 'Trending Effect 2'],
            'effect_categories': ['Face', 'Body', 'Environment'],
            'usage_patterns': {
                'average_use_count': 5000,
                'trend_duration': '5-10 days',
                'best_use_times': ['Early Trend', 'Peak Trend']
            }
        }
    
    def _track_tiktok_series_trends(self):
        """Track TikTok Series trends"""
        return {
            'top_series_types': ['Tutorial Series', 'Challenge Series', 'Story Series'],
            'optimal_episodes': '3-5',
            'best_series_topics': ['How-to Guides', 'Challenges', 'Behind the Scenes']
        }
    
    def _track_tiktok_live_trends(self):
        """Track TikTok Live trends"""
        return {
            'top_live_formats': ['Q&A', 'Tutorial', 'Behind the Scenes'],
            'optimal_duration': '15-30 minutes',
            'best_streaming_times': ['Evening', 'Weekend'],
            'engagement_tools': ['Gifts', 'Comments', 'Questions']
        }

    def get_platform_features(self, platform):
        """Get current platform-specific features and trends"""
        if platform not in self.platform_features:
            return {}
        
        current_time = datetime.now()
        if (platform in self.trending_cache and 
            current_time - self.trending_cache[platform]['timestamp'] < self.cache_expiry):
            return self.trending_cache[platform]['data']
        
        features = {}
        for feature_name, tracking_func in self.platform_features[platform].items():
            features[feature_name] = tracking_func()
        
        self.trending_cache[platform] = {
            'data': features,
            'timestamp': current_time
        }
        
        return features

    def _analyze_hashtag_trends(self, platform, niche):
        """Analyze trending hashtags for a platform and niche"""
        # This would be implemented with platform-specific APIs
        return [
            {'tag': f'#{niche}trending', 'volume': 10000, 'growth': 0.15},
            {'tag': f'#{niche}viral', 'volume': 8000, 'growth': 0.12},
            {'tag': f'#{platform}{niche}', 'volume': 6000, 'growth': 0.10}
        ]
    
    def _analyze_topic_trends(self, platform, niche):
        """Analyze trending topics for a platform and niche"""
        return [
            {'topic': f'Latest in {niche}', 'engagement': 0.25, 'sentiment': 0.8},
            {'topic': f'{niche} tips and tricks', 'engagement': 0.18, 'sentiment': 0.9},
            {'topic': f'{platform} {niche} trends', 'engagement': 0.20, 'sentiment': 0.85}
        ]
    
    def _analyze_keyword_trends(self, platform, niche):
        """Analyze trending keywords for a platform and niche"""
        return [
            {'keyword': niche, 'difficulty': 0.3, 'opportunity': 0.7},
            {'keyword': f'{niche} content', 'difficulty': 0.4, 'opportunity': 0.6},
            {'keyword': f'{platform} {niche}', 'difficulty': 0.5, 'opportunity': 0.5}
        ]

    def _get_platform_insights(self, platform, content_data):
        """Get platform-specific insights and best practices"""
        features = self.get_platform_features(platform)
        
        insights = {
            'optimal_content_length': self._calculate_optimal_length(content_data),
            'best_publishing_times': self._analyze_publishing_times(content_data),
            'top_performing_features': self._analyze_top_features(content_data),
            'platform_specific_trends': features
        }
        
        return insights

    def _calculate_optimal_length(self, content_data):
        """Calculate optimal content length based on engagement"""
        lengths = []
        engagements = []
        
        for content in content_data:
            if 'duration' in content:
                lengths.append(content['duration'])
                engagements.append(content.get('engagement_metrics', {}).get('views', 0))
        
        if not lengths:
            return None
        
        # Weight lengths by engagement
        weighted_lengths = np.average(lengths, weights=engagements)
        return weighted_lengths
    
    def _analyze_publishing_times(self, content_data):
        """Analyze best publishing times based on engagement"""
        time_engagement = {}
        
        for content in content_data:
            if 'timestamp' in content:
                hour = content['timestamp'].hour
                engagement = content.get('engagement_metrics', {}).get('views', 0)
                if hour not in time_engagement:
                    time_engagement[hour] = []
                time_engagement[hour].append(engagement)
        
        # Calculate average engagement by hour
        avg_engagement = {hour: np.mean(engagements) for hour, engagements in time_engagement.items()}
        best_times = sorted(avg_engagement.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return [f"{hour:02d}:00" for hour, _ in best_times]
    
    def _analyze_top_features(self, content_data):
        """Analyze top performing content features"""
        features = {
            'hooks': Counter(),
            'hashtags': Counter(),
            'content_types': Counter(),
            'engagement_patterns': {}
        }
        
        for content in content_data:
            # Analyze hooks
            if 'hook_analysis' in content:
                for hook, value in content['hook_analysis'].items():
                    if value:
                        features['hooks'][hook] += 1
            
            # Analyze hashtags
            if 'hashtags' in content:
                for hashtag in content['hashtags']:
                    features['hashtags'][hashtag] += 1
            
            # Analyze content types
            if 'content_type' in content:
                features['content_types'][content['content_type']] += 1
            
            # Analyze engagement patterns
            if 'engagement_metrics' in content:
                for metric, value in content['engagement_metrics'].items():
                    if metric not in features['engagement_patterns']:
                        features['engagement_patterns'][metric] = []
                    features['engagement_patterns'][metric].append(value)
        
        # Calculate average engagement metrics
        for metric, values in features['engagement_patterns'].items():
            features['engagement_patterns'][metric] = np.mean(values)
        
        return features

    def optimize_content(self, content_data, platform, niche):
        """Optimize content with advanced analysis"""
        # Get trending topics
        trends = self.get_trending_topics(platform, niche)
        
        # Predict virality
        virality_scores = self.predict_virality(content_data)
        
        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(content_data, virality_scores)
        
        # Sort by virality score
        sorted_recommendations = sorted(recommendations, key=lambda x: x['virality_score'], reverse=True)
        
        return {
            'trending_topics': trends,
            'optimization_recommendations': sorted_recommendations,
            'top_performing_patterns': self._extract_top_patterns(content_data, virality_scores),
            'platform_specific_insights': self._get_platform_insights(platform, content_data)
        }

    def _extract_top_patterns(self, content_data, virality_scores):
        """Extract advanced patterns from top-performing content"""
        top_content = [content for content, score in zip(content_data, virality_scores) 
                      if score > 0.7]
        
        patterns = {
            'common_hooks': {},
            'content_length': [],
            'engagement_patterns': {},
            'time_patterns': {},
            'sentiment_patterns': [],
            'keyword_patterns': {}
        }
        
        for content in top_content:
            # Analyze hooks
            hooks = content.get('hook_analysis', {})
            for hook, value in hooks.items():
                if value:
                    patterns['common_hooks'][hook] = patterns['common_hooks'].get(hook, 0) + 1
            
            # Analyze content length
            length = len(content.get('title', '') + content.get('description', ''))
            patterns['content_length'].append(length)
            
            # Analyze engagement patterns
            engagement = content.get('engagement_metrics', {})
            for metric, value in engagement.items():
                patterns['engagement_patterns'][metric] = patterns['engagement_patterns'].get(metric, 0) + value
            
            # Analyze sentiment
            text = content.get('title', '') + ' ' + content.get('description', '')
            sentiment = self.sia.polarity_scores(text)
            patterns['sentiment_patterns'].append(sentiment['compound'])
            
            # Extract keywords
            tokens = word_tokenize(text.lower())
            words = [word for word in tokens if word.isalpha() and word not in stopwords.words('english')]
            for word in words:
                patterns['keyword_patterns'][word] = patterns['keyword_patterns'].get(word, 0) + 1
        
        # Calculate advanced metrics
        return {
            'most_effective_hooks': sorted(patterns['common_hooks'].items(), 
                                         key=lambda x: x[1], reverse=True)[:3],
            'optimal_content_length': {
                'mean': np.mean(patterns['content_length']),
                'median': np.median(patterns['content_length']),
                'std': np.std(patterns['content_length'])
            },
            'engagement_ratios': {k: v/len(top_content) for k, v in patterns['engagement_patterns'].items()},
            'sentiment_distribution': {
                'mean': np.mean(patterns['sentiment_patterns']),
                'std': np.std(patterns['sentiment_patterns'])
            },
            'top_keywords': sorted(patterns['keyword_patterns'].items(), 
                                 key=lambda x: x[1], reverse=True)[:10]
        }

    def analyze_creator_performance(self, creator_data):
        """Analyze creator performance metrics"""
        performance = {
            'follower_growth': self._calculate_growth_rate(creator_data),
            'engagement_ratio': self._calculate_engagement_ratio(creator_data),
            'virality_score': self._calculate_virality_score(creator_data),
            'posting_consistency': self._analyze_posting_consistency(creator_data),
            'monetization_signals': self._analyze_monetization_signals(creator_data)
        }
        return performance

    def _calculate_growth_rate(self, creator_data):
        """Calculate follower growth rate"""
        if len(creator_data) < 2:
            return 0
        
        current_followers = creator_data[-1].get('follower_count', 0)
        previous_followers = creator_data[0].get('follower_count', 0)
        days = (creator_data[-1]['timestamp'] - creator_data[0]['timestamp']).days
        
        if days == 0 or previous_followers == 0:
            return 0
        
        return ((current_followers - previous_followers) / previous_followers) / days

    def _calculate_engagement_ratio(self, creator_data):
        """Calculate average engagement ratio"""
        total_engagement = 0
        total_views = 0
        
        for post in creator_data:
            engagement = post.get('engagement_metrics', {})
            total_engagement += engagement.get('likes', 0) + engagement.get('comments', 0)
            total_views += engagement.get('views', 0)
        
        return total_engagement / total_views if total_views > 0 else 0

    def _calculate_virality_score(self, creator_data):
        """Calculate content virality score"""
        viral_posts = 0
        total_posts = len(creator_data)
        
        for post in creator_data:
            engagement = post.get('engagement_metrics', {})
            views = engagement.get('views', 0)
            followers = post.get('follower_count', 0)
            
            if followers > 0 and views / followers > 2:  # More than 2x followers
                viral_posts += 1
        
        return viral_posts / total_posts if total_posts > 0 else 0

    def _analyze_posting_consistency(self, creator_data):
        """Analyze posting frequency and consistency"""
        if len(creator_data) < 2:
            return {'frequency': 0, 'consistency_score': 0}
        
        timestamps = [post['timestamp'] for post in creator_data]
        time_diffs = [(timestamps[i+1] - timestamps[i]).days for i in range(len(timestamps)-1)]
        
        avg_frequency = np.mean(time_diffs)
        consistency_score = 1 - (np.std(time_diffs) / avg_frequency if avg_frequency > 0 else 1)
        
        return {
            'frequency': 1 / avg_frequency if avg_frequency > 0 else 0,
            'consistency_score': max(0, min(1, consistency_score))
        }

    def _analyze_monetization_signals(self, creator_data):
        """Analyze monetization strategies"""
        signals = {
            'digital_products': False,
            'services': False,
            'affiliate_marketing': False,
            'funnel_links': False,
            'sponsorships': False
        }
        
        for post in creator_data:
            text = post.get('title', '') + ' ' + post.get('description', '')
            bio = post.get('bio', '')
            
            # Check for digital product signals
            if any(term in text.lower() for term in ['course', 'ebook', 'template', 'download']):
                signals['digital_products'] = True
            
            # Check for service signals
            if any(term in text.lower() for term in ['consult', 'coach', 'service', 'book a call']):
                signals['services'] = True
            
            # Check for affiliate signals
            if any(term in text.lower() for term in ['affiliate', 'partner', 'sponsored', 'commission']):
                signals['affiliate_marketing'] = True
            
            # Check for funnel signals
            if any(term in bio.lower() for term in ['link in bio', 'linktree', 'beacons', 'website']):
                signals['funnel_links'] = True
            
            # Check for sponsorship signals
            if any(term in text.lower() for term in ['sponsored', 'partner', 'collab', 'brand']):
                signals['sponsorships'] = True
        
        return signals

    def extract_viral_patterns(self, content_data):
        """Extract and cluster viral content patterns"""
        patterns = {
            'hooks': self._analyze_hooks(content_data),
            'captions': self._analyze_captions(content_data),
            'hashtags': self._analyze_hashtags(content_data),
            'visual_elements': self._analyze_visual_elements(content_data),
            'ctas': self._analyze_ctas(content_data)
        }
        
        return patterns

    def _analyze_hooks(self, content_data):
        """Analyze hook types and effectiveness"""
        hook_patterns = []
        
        for content in content_data:
            text = content.get('title', '') + ' ' + content.get('description', '')
            engagement = content.get('engagement_metrics', {})
            views = engagement.get('views', 0)
            
            for hook_type, patterns in self.hook_types.items():
                for pattern in patterns:
                    if pattern.lower() in text.lower():
                        hook_patterns.append({
                            'type': hook_type,
                            'pattern': pattern,
                            'views': views,
                            'effectiveness': views / content.get('follower_count', 1)
                        })
        
        return sorted(hook_patterns, key=lambda x: x['effectiveness'], reverse=True)

    def _analyze_captions(self, content_data):
        """Analyze caption styles and effectiveness"""
        caption_patterns = []
        
        for content in content_data:
            caption = content.get('description', '')
            engagement = content.get('engagement_metrics', {})
            
            # Analyze caption length
            length = len(caption.split())
            
            # Analyze emoji usage
            emoji_count = len(re.findall(r'[\U0001F300-\U0001F9FF]', caption))
            
            # Analyze line breaks
            line_breaks = caption.count('\n')
            
            caption_patterns.append({
                'length': length,
                'emoji_count': emoji_count,
                'line_breaks': line_breaks,
                'engagement': engagement.get('likes', 0) + engagement.get('comments', 0)
            })
        
        return caption_patterns

    def _analyze_hashtags(self, content_data):
        """Analyze hashtag usage and effectiveness"""
        hashtag_patterns = Counter()
        
        for content in content_data:
            hashtags = re.findall(r'#\w+', content.get('description', ''))
            engagement = content.get('engagement_metrics', {})
            
            for hashtag in hashtags:
                hashtag_patterns[hashtag.lower()] += engagement.get('likes', 0)
        
        return hashtag_patterns.most_common(20)

    def _analyze_visual_elements(self, content_data):
        """Analyze visual elements and their impact"""
        visual_patterns = []
        
        for content in content_data:
            elements = content.get('visual_elements', {})
            engagement = content.get('engagement_metrics', {})
            
            pattern = {
                'text_overlay': elements.get('text_overlay', False),
                'editing_speed': elements.get('editing_speed', 0),
                'music_style': elements.get('music_style', ''),
                'engagement': engagement.get('views', 0)
            }
            
            visual_patterns.append(pattern)
        
        return visual_patterns

    def _analyze_ctas(self, content_data):
        """Analyze call-to-action effectiveness"""
        cta_patterns = []
        
        for content in content_data:
            text = content.get('title', '') + ' ' + content.get('description', '')
            engagement = content.get('engagement_metrics', {})
            
            for cta_type, pattern in self.cta_formats.items():
                if pattern.lower() in text.lower():
                    cta_patterns.append({
                        'type': cta_type,
                        'pattern': pattern,
                        'engagement': engagement.get('likes', 0) + engagement.get('comments', 0)
                    })
        
        return sorted(cta_patterns, key=lambda x: x['engagement'], reverse=True)

    def generate_content_framework(self, patterns):
        """Generate content framework based on analyzed patterns"""
        framework = {
            'viral_hooks': self._extract_top_hooks(patterns['hooks']),
            'storytelling_angles': self._extract_storytelling_angles(patterns['captions']),
            'cta_formats': self._extract_cta_formats(patterns['ctas']),
            'posting_cadence': self._determine_posting_cadence(patterns['captions']),
            'hashtag_strategy': self._create_hashtag_strategy(patterns['hashtags']),
            'visual_guidelines': self._create_visual_guidelines(patterns['visual_elements'])
        }
        
        return framework

    def _extract_top_hooks(self, hook_patterns):
        """Extract top performing hooks"""
        return sorted(hook_patterns, key=lambda x: x['effectiveness'], reverse=True)[:10]

    def _extract_storytelling_angles(self, caption_patterns):
        """Extract effective storytelling angles"""
        # Cluster captions by length and engagement
        X = np.array([[p['length'], p['engagement']] for p in caption_patterns])
        kmeans = KMeans(n_clusters=5, random_state=42).fit(X)
        
        # Return top angles based on cluster centers
        return sorted(self.storytelling_angles.items(), 
                     key=lambda x: np.mean([p['engagement'] for p in caption_patterns 
                                          if kmeans.predict([[p['length'], p['engagement']]])[0] == 
                                          np.argmax(kmeans.cluster_centers_[:, 1])]),
                     reverse=True)[:10]

    def _extract_cta_formats(self, cta_patterns):
        """Extract most effective CTA formats"""
        return sorted(cta_patterns, key=lambda x: x['engagement'], reverse=True)[:10]

    def _determine_posting_cadence(self, caption_patterns):
        """Determine optimal posting cadence"""
        # Analyze engagement patterns by day of week and hour
        posting_times = []
        
        for pattern in caption_patterns:
            if 'timestamp' in pattern:
                posting_times.append({
                    'day_of_week': pattern['timestamp'].weekday(),
                    'hour': pattern['timestamp'].hour,
                    'engagement': pattern['engagement']
                })
        
        # Group by day and hour, calculate average engagement
        engagement_by_time = {}
        for time in posting_times:
            key = (time['day_of_week'], time['hour'])
            if key not in engagement_by_time:
                engagement_by_time[key] = []
            engagement_by_time[key].append(time['engagement'])
        
        # Calculate average engagement for each time slot
        avg_engagement = {k: np.mean(v) for k, v in engagement_by_time.items()}
        
        # Return top 5 posting times
        return sorted(avg_engagement.items(), key=lambda x: x[1], reverse=True)[:5]

    def _create_hashtag_strategy(self, hashtag_patterns):
        """Create optimal hashtag strategy"""
        return {
            'primary_hashtags': hashtag_patterns[:5],
            'secondary_hashtags': hashtag_patterns[5:15],
            'niche_hashtags': [h for h in hashtag_patterns if h[0].startswith('#niche')],
            'trending_hashtags': [h for h in hashtag_patterns if h[0].startswith('#trend')]
        }

    def _create_visual_guidelines(self, visual_patterns):
        """Create visual content guidelines"""
        guidelines = {
            'text_overlay': {
                'recommended': any(p['text_overlay'] for p in visual_patterns),
                'best_practices': []
            },
            'editing_speed': {
                'optimal': np.median([p['editing_speed'] for p in visual_patterns]),
                'range': (np.percentile([p['editing_speed'] for p in visual_patterns], 25),
                         np.percentile([p['editing_speed'] for p in visual_patterns], 75))
            },
            'music_style': Counter([p['music_style'] for p in visual_patterns]).most_common(3)
        }
        
        return guidelines

    def generate_monetization_blueprint(self, creator_data):
        """Generate monetization strategy blueprint"""
        blueprint = {
            'current_monetization': self._analyze_monetization_signals(creator_data),
            'recommended_paths': self._suggest_monetization_paths(creator_data),
            'revenue_model': self._create_revenue_model(creator_data)
        }
        
        return blueprint

    def _suggest_monetization_paths(self, creator_data):
        """Suggest monetization paths based on content and audience"""
        paths = {
            'minimum_viable': [],
            'high_ticket': [],
            'recurring': []
        }
        
        # Analyze content type and engagement
        content_types = Counter()
        for post in creator_data:
            if 'tutorial' in post.get('description', '').lower():
                content_types['educational'] += 1
            elif 'review' in post.get('description', '').lower():
                content_types['review'] += 1
            elif 'story' in post.get('description', '').lower():
                content_types['storytelling'] += 1
        
        # Suggest paths based on content type
        if content_types['educational'] > content_types['review']:
            paths['minimum_viable'].append('Digital guide or template')
            paths['high_ticket'].append('Online course or masterclass')
            paths['recurring'].append('Membership community')
        elif content_types['review'] > content_types['educational']:
            paths['minimum_viable'].append('Affiliate marketing')
            paths['high_ticket'].append('Brand partnerships')
            paths['recurring'].append('Product subscription')
        else:
            paths['minimum_viable'].append('Ebook or digital product')
            paths['high_ticket'].append('Coaching or consulting')
            paths['recurring'].append('Content subscription')
        
        return paths

    def _create_revenue_model(self, creator_data):
        """Create detailed revenue model"""
        model = {
            'lead_magnet': self._suggest_lead_magnet(creator_data),
            'funnel_type': self._determine_funnel_type(creator_data),
            'upsell_path': self._create_upsell_path(creator_data),
            'pricing_strategy': self._determine_pricing(creator_data)
        }
        
        return model

    def _suggest_lead_magnet(self, creator_data):
        """Suggest optimal lead magnet based on content"""
        content_types = Counter()
        for post in creator_data:
            if 'how to' in post.get('description', '').lower():
                content_types['tutorial'] += 1
            elif 'tips' in post.get('description', '').lower():
                content_types['tips'] += 1
            elif 'guide' in post.get('description', '').lower():
                content_types['guide'] += 1
        
        if content_types['tutorial'] > content_types['tips']:
            return 'Step-by-step guide or checklist'
        elif content_types['tips'] > content_types['guide']:
            return 'Quick tips PDF or video series'
        else:
            return 'Resource guide or template pack'

    def _determine_funnel_type(self, creator_data):
        """Determine optimal funnel type"""
        engagement = self._calculate_engagement_ratio(creator_data)
        if engagement > 0.1:  # High engagement
            return 'Value ladder funnel'
        else:
            return 'Tripwire funnel'

    def _create_upsell_path(self, creator_data):
        """Create upsell path based on content and audience"""
        path = {
            'entry': self._suggest_lead_magnet(creator_data),
            'mid_tier': 'Workshop or mini-course',
            'high_tier': 'Mastermind or coaching program'
        }
        
        return path

    def _determine_pricing(self, creator_data):
        """Determine optimal pricing strategy"""
        engagement = self._calculate_engagement_ratio(creator_data)
        follower_count = creator_data[-1].get('follower_count', 0)
        
        return {
            'entry_level': '$27-$47',
            'mid_tier': '$197-$497',
            'high_tier': '$997-$1997',
            'subscription': '$27-$97/month'
        }

    def generate_content_calendar(self, framework, days=30):
        """Generate 30-day content calendar"""
        calendar = []
        
        for day in range(days):
            date = datetime.now() + timedelta(days=day)
            
            # Select content type based on day of week
            if date.weekday() in [0, 3]:  # Monday, Thursday
                content_type = 'educational'
            elif date.weekday() in [2, 5]:  # Wednesday, Saturday
                content_type = 'entertainment'
            else:
                content_type = 'engagement'
            
            # Select hook and angle
            hook = np.random.choice(framework['viral_hooks'])
            angle = np.random.choice(framework['storytelling_angles'])
            
            # Create content plan
            plan = {
                'date': date.strftime('%Y-%m-%d'),
                'content_type': content_type,
                'hook': hook,
                'angle': angle,
                'hashtags': self._select_hashtags(framework['hashtag_strategy']),
                'cta': np.random.choice(framework['cta_formats']),
                'visual_guidelines': framework['visual_guidelines']
            }
            
            calendar.append(plan)
        
        return calendar

    def _select_hashtags(self, hashtag_strategy):
        """Select optimal hashtag combination"""
        return (
            [h[0] for h in hashtag_strategy['primary_hashtags'][:2]] +
            [h[0] for h in hashtag_strategy['secondary_hashtags'][:3]] +
            [h[0] for h in hashtag_strategy['niche_hashtags'][:2]] +
            [h[0] for h in hashtag_strategy['trending_hashtags'][:1]]
        ) 