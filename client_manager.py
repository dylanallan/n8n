import json
import os
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pandas as pd
from viral_analyzer import ViralContentAnalyzer

class ClientManager:
    def __init__(self):
        self.clients_file = 'clients.json'
        self.clients = self._load_clients()
        self.viral_analyzer = ViralContentAnalyzer()
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.creds = None

    def _load_clients(self):
        """Load existing clients from JSON file"""
        if os.path.exists(self.clients_file):
            with open(self.clients_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_clients(self):
        """Save clients to JSON file"""
        with open(self.clients_file, 'w') as f:
            json.dump(self.clients, f, indent=4)

    def get_google_credentials(self):
        """Get or refresh Google Drive credentials"""
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        
        return self.creds

    def create_google_doc(self, client_id, content):
        """Create a Google Doc with the analysis results"""
        try:
            service = build('docs', 'v1', credentials=self.get_google_credentials())
            drive_service = build('drive', 'v3', credentials=self.get_google_credentials())
            
            # Create the document
            doc = service.documents().create(body={
                'title': f'Content Analysis - {client_id} - {datetime.now().strftime("%Y-%m-%d")}'
            }).execute()
            
            # Add content to the document
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }
            ]
            
            service.documents().batchUpdate(
                documentId=doc.get('documentId'),
                body={'requests': requests}
            ).execute()
            
            # Share the document with the client's email
            if client_id in self.clients:
                drive_service.permissions().create(
                    fileId=doc.get('documentId'),
                    body={'type': 'user', 'role': 'writer', 'emailAddress': self.clients[client_id]['email']},
                    fields='id'
                ).execute()
            
            return doc.get('documentId')
            
        except Exception as e:
            print(f"Error creating Google Doc: {e}")
            return None

    def analyze_social_platforms(self, platform_data):
        """Analyze client's social media platforms and provide optimization suggestions"""
        analysis = {}
        
        for platform, data in platform_data.items():
            platform_analysis = {
                'current_performance': self.viral_analyzer.analyze_creator_performance(data['content']),
                'optimization_suggestions': [],
                'trending_features': self.viral_analyzer.get_trending_topics(platform, data.get('niche', '')),
                'platform_specific_insights': self.viral_analyzer._get_platform_insights(platform, data['content'])
            }
            
            # Generate optimization suggestions
            if platform == 'youtube':
                suggestions = [
                    'Optimize video titles and descriptions with trending keywords',
                    'Use YouTube Shorts for increased reach',
                    'Implement YouTube Community tab for better engagement',
                    'Create playlists to improve watch time',
                    'Use end screens and cards for better navigation'
                ]
            elif platform == 'instagram':
                suggestions = [
                    'Utilize Instagram Reels for viral potential',
                    'Implement Instagram Guides for content organization',
                    'Use Instagram Stories for daily engagement',
                    'Create Instagram Highlights for evergreen content',
                    'Optimize Instagram bio with clear call-to-action'
                ]
            elif platform == 'tiktok':
                suggestions = [
                    'Use trending sounds and hashtags',
                    'Create TikTok Series for content organization',
                    'Implement TikTok LIVE for real-time engagement',
                    'Use TikTok Effects for creative content',
                    'Optimize TikTok profile with clear branding'
                ]
            
            platform_analysis['optimization_suggestions'] = suggestions
            analysis[platform] = platform_analysis
        
        return analysis

    def onboard_new_client(self):
        """Onboard a new client with enhanced social media analysis"""
        print("\n=== New Client Onboarding ===")
        
        # Basic client information
        client_id = input("Enter client ID: ")
        name = input("Enter client name: ")
        email = input("Enter client email: ")
        niche = input("Enter niche: ")
        specific_requirements = input("Enter specific requirements (comma-separated): ").split(',')
        competitors = input("Enter competitors to track (comma-separated): ").split(',')
        
        # Social media platform analysis
        print("\n=== Social Media Platform Analysis ===")
        platform_data = {}
        
        for platform in ['youtube', 'instagram', 'tiktok']:
            print(f"\nAnalyzing {platform.capitalize()}...")
            channel_id = input(f"Enter {platform} channel ID/username (or press Enter to skip): ")
            if channel_id:
                # Fetch and analyze platform data
                platform_data[platform] = {
                    'channel_id': channel_id,
                    'niche': niche,
                    'content': []  # This would be populated with actual content data
                }
        
        # Analyze platforms and generate suggestions
        platform_analysis = self.analyze_social_platforms(platform_data)
        
        # Create client record
        client_data = {
            'name': name,
            'email': email,
            'niche': niche,
            'specific_requirements': specific_requirements,
            'competitors': competitors,
            'platforms': platform_data,
            'platform_analysis': platform_analysis,
            'last_analysis': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        self.clients[client_id] = client_data
        self._save_clients()
        
        # Generate initial optimization report
        self._generate_initial_optimization_report(client_id, platform_analysis)
        
        return client_id

    def _generate_initial_optimization_report(self, client_id, platform_analysis):
        """Generate initial optimization report for new clients"""
        report_content = f"🧠 Initial Platform Optimization Report\n\n"
        report_content += f"Client: {self.clients[client_id]['name']}\n"
        report_content += f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        for platform, analysis in platform_analysis.items():
            report_content += f"=== {platform.upper()} Analysis ===\n\n"
            
            # Current Performance
            report_content += "📊 Current Performance:\n"
            performance = analysis['current_performance']
            report_content += f"Follower Growth: {performance['follower_growth']:.2%} per day\n"
            report_content += f"Engagement Ratio: {performance['engagement_ratio']:.2%}\n"
            report_content += f"Virality Score: {performance['virality_score']:.2%}\n"
            report_content += f"Posting Consistency: {performance['posting_consistency']['consistency_score']:.2%}\n\n"
            
            # Optimization Suggestions
            report_content += "🎯 Optimization Suggestions:\n"
            for suggestion in analysis['optimization_suggestions']:
                report_content += f"- {suggestion}\n"
            
            # Trending Features
            report_content += "\n📈 Trending Features:\n"
            trends = analysis['trending_features']
            report_content += "Hashtags:\n"
            for tag in trends['hashtags']:
                report_content += f"- {tag['tag']} (Volume: {tag['volume']}, Growth: {tag['growth']:.2%})\n"
            
            report_content += "\nTopics:\n"
            for topic in trends['topics']:
                report_content += f"- {topic['topic']} (Engagement: {topic['engagement']:.2%}, Sentiment: {topic['sentiment']:.2%})\n"
            
            # Platform-Specific Insights
            report_content += "\n🔍 Platform-Specific Insights:\n"
            insights = analysis['platform_specific_insights']
            for key, value in insights.items():
                report_content += f"{key.replace('_', ' ').title()}: {value}\n"
            
            report_content += "\n"
        
        # Create Google Doc with report
        doc_id = self.create_google_doc(client_id, report_content)
        if doc_id:
            print(f"\nInitial optimization report created and shared: https://docs.google.com/document/d/{doc_id}")

    def select_client(self):
        """Select an existing client or onboard a new one"""
        if not self.clients:
            print("No existing clients found. Starting new client onboarding...")
            return self.onboard_new_client()
        
        print("\nExisting Clients:")
        for client_id, client in self.clients.items():
            print(f"{client_id}: {client['name']} ({client['niche']})")
        
        choice = input("\nEnter client ID to select, or 'new' to onboard a new client: ")
        
        if choice.lower() == 'new':
            return self.onboard_new_client()
        elif choice in self.clients:
            return choice
        else:
            print("Invalid selection. Please try again.")
            return self.select_client()

    def update_client_analysis(self, client_id, analysis_date):
        """Update the last analysis date for a client"""
        if client_id in self.clients:
            self.clients[client_id]['last_analysis'] = analysis_date
            self._save_clients()

    def get_client_info(self, client_id):
        """Get information for a specific client"""
        return self.clients.get(client_id) 