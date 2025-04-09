import os
from datetime import datetime
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from youtube_scraper import YouTubeScraper
from instagram_scraper import InstagramScraper
from tiktok_scraper import TikTokScraper
from client_manager import ClientManager
from viral_analyzer import ViralContentAnalyzer
from config import OUTPUT_DIR, SPREADSHEET_NAME, PLATFORMS

app = FastAPI()

class ContentAnalyzer:
    def __init__(self):
        self.youtube_scraper = YouTubeScraper()
        self.instagram_scraper = InstagramScraper()
        self.tiktok_scraper = TikTokScraper()
        self.client_manager = ClientManager()
        self.viral_analyzer = ViralContentAnalyzer()
        
        # Create output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

    def analyze_niche(self, client_id):
        """Analyze content across all platforms for a specific client's niche"""
        client_info = self.client_manager.get_client_info(client_id)
        if not client_info:
            print("Client not found!")
            return
        
        niche = client_info['niche']
        results = {}
        all_content = []
        creator_data = {}
        
        print(f"\nAnalyzing content for client: {client_info['name']}")
        print(f"Niche: {niche}")
        print(f"Specific requirements: {client_info['specific_requirements']}")
        print(f"Competitors to track: {', '.join(client_info['competitors'])}")
        
        # Analyze YouTube content
        if 'youtube' in PLATFORMS:
            print(f"\nAnalyzing YouTube content for niche: {niche}")
            youtube_creators = self.youtube_scraper.get_top_creators(niche)
            youtube_results = []
            
            for creator in youtube_creators:
                print(f"\nAnalyzing creator: {creator['channel_name']}")
                videos = self.youtube_scraper.get_top_videos(creator['channel_id'])
                analysis = self.youtube_scraper.analyze_content(videos)
                youtube_results.extend(analysis)
                all_content.extend(analysis)
                
                # Analyze creator performance
                creator_data[f"youtube_{creator['channel_id']}"] = {
                    'platform': 'youtube',
                    'creator_info': creator,
                    'content': analysis,
                    'performance': self.viral_analyzer.analyze_creator_performance(analysis)
                }
            
            results['youtube'] = youtube_results
            self._save_platform_results('youtube', niche, youtube_results)

        # Analyze Instagram content
        if 'instagram' in PLATFORMS:
            print(f"\nAnalyzing Instagram content for niche: {niche}")
            instagram_creators = self.instagram_scraper.get_top_creators(niche)
            instagram_results = []
            
            for creator in instagram_creators:
                print(f"\nAnalyzing creator: {creator['username']}")
                posts = self.instagram_scraper.get_top_posts(creator['username'])
                analysis = self.instagram_scraper.analyze_content(posts)
                instagram_results.extend(analysis)
                all_content.extend(analysis)
                
                # Analyze creator performance
                creator_data[f"instagram_{creator['username']}"] = {
                    'platform': 'instagram',
                    'creator_info': creator,
                    'content': analysis,
                    'performance': self.viral_analyzer.analyze_creator_performance(analysis)
                }
            
            results['instagram'] = instagram_results
            self._save_platform_results('instagram', niche, instagram_results)

        # Analyze TikTok content
        if 'tiktok' in PLATFORMS:
            print(f"\nAnalyzing TikTok content for niche: {niche}")
            tiktok_creators = self.tiktok_scraper.get_top_creators(niche)
            tiktok_results = []
            
            for creator in tiktok_creators:
                print(f"\nAnalyzing creator: {creator['username']}")
                videos = self.tiktok_scraper.get_top_videos(creator['username'])
                analysis = self.tiktok_scraper.analyze_content(videos)
                tiktok_results.extend(analysis)
                all_content.extend(analysis)
                
                # Analyze creator performance
                creator_data[f"tiktok_{creator['username']}"] = {
                    'platform': 'tiktok',
                    'creator_info': creator,
                    'content': analysis,
                    'performance': self.viral_analyzer.analyze_creator_performance(analysis)
                }
            
            results['tiktok'] = tiktok_results
            self._save_platform_results('tiktok', niche, tiktok_results)

        # Train viral content model if needed
        if len(all_content) > 0:
            print("\nTraining viral content prediction model...")
            self.viral_analyzer.train_model(all_content)

        # Generate viral content analysis
        viral_analysis = {}
        for platform, platform_results in results.items():
            print(f"\nAnalyzing viral potential for {platform} content...")
            viral_analysis[platform] = self.viral_analyzer.optimize_content(
                platform_results, platform, niche
            )

        # Extract viral patterns
        print("\nExtracting viral patterns...")
        patterns = self.viral_analyzer.extract_viral_patterns(all_content)
        
        # Generate content framework
        print("\nGenerating content framework...")
        content_framework = self.viral_analyzer.generate_content_framework(patterns)
        
        # Generate monetization blueprint
        print("\nGenerating monetization blueprint...")
        monetization_blueprint = self.viral_analyzer.generate_monetization_blueprint(all_content)
        
        # Generate content calendar
        print("\nGenerating content calendar...")
        content_calendar = self.viral_analyzer.generate_content_calendar(content_framework)

        # Generate combined analysis
        combined_analysis = self._generate_combined_analysis(
            niche, results, viral_analysis, 
            content_framework, monetization_blueprint,
            content_calendar, creator_data
        )
        
        # Create Google Doc with results
        doc_content = self._format_doc_content(
            client_info, combined_analysis, 
            viral_analysis, content_framework,
            monetization_blueprint, content_calendar,
            creator_data
        )
        doc_id = self.client_manager.create_google_doc(client_id, doc_content)
        
        if doc_id:
            print(f"\nAnalysis document created and shared with client: https://docs.google.com/document/d/{doc_id}")
        
        # Update client's last analysis date
        self.client_manager.update_client_analysis(client_id, datetime.now().isoformat())
        
        return results

    def _save_platform_results(self, platform, niche, results):
        """Save platform-specific results to a spreadsheet"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(OUTPUT_DIR, f'{platform}_{niche}_{timestamp}.xlsx')
        
        if platform == 'youtube':
            self.youtube_scraper.save_to_spreadsheet(results, filename)
        elif platform == 'instagram':
            self.instagram_scraper.save_to_spreadsheet(results, filename)
        elif platform == 'tiktok':
            self.tiktok_scraper.save_to_spreadsheet(results, filename)

    def _generate_combined_analysis(self, niche, results, viral_analysis, 
                                  content_framework, monetization_blueprint,
                                  content_calendar, creator_data):
        """Generate a combined analysis across all platforms"""
        combined_data = []
        
        for platform, platform_results in results.items():
            for result in platform_results:
                combined_data.append({
                    'platform': platform,
                    'content_id': result.get('video_id') or result.get('post_id'),
                    'content': result.get('title') or result.get('caption') or result.get('description'),
                    'hook_analysis': result.get('hook_analysis', {}),
                    'engagement_metrics': result.get('engagement_metrics', {}),
                    'viral_analysis': viral_analysis.get(platform, {}).get('optimization_recommendations', []),
                    'platform_insights': viral_analysis.get(platform, {}).get('platform_specific_insights', {})
                })
        
        return {
            'content_data': combined_data,
            'content_framework': content_framework,
            'monetization_blueprint': monetization_blueprint,
            'content_calendar': content_calendar,
            'creator_data': creator_data
        }

    def _format_doc_content(self, client_info, combined_analysis, 
                          viral_analysis, content_framework,
                          monetization_blueprint, content_calendar,
                          creator_data):
        """Format analysis results for Google Doc"""
        content = f"🧠 Niche Deep Dive Summary\n\n"
        content += f"Client: {client_info['name']}\n"
        content += f"Niche: {client_info['niche']}\n"
        content += f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        content += "📊 Top 10 Creators & Strategy Matrix\n\n"
        for creator_id, data in creator_data.items():
            content += f"Creator: {data['creator_info'].get('channel_name', data['creator_info'].get('username'))}\n"
            content += f"Platform: {data['platform']}\n"
            content += f"Follower Growth: {data['performance']['follower_growth']:.2%} per day\n"
            content += f"Engagement Ratio: {data['performance']['engagement_ratio']:.2%}\n"
            content += f"Virality Score: {data['performance']['virality_score']:.2%}\n"
            content += f"Posting Consistency: {data['performance']['posting_consistency']['consistency_score']:.2%}\n"
            content += "Monetization Signals:\n"
            for signal, active in data['performance']['monetization_signals'].items():
                if active:
                    content += f"- {signal.replace('_', ' ').title()}\n"
            content += "\n"
        
        content += "📅 30-Day Viral Content Plan\n\n"
        for day in content_calendar:
            content += f"Date: {day['date']}\n"
            content += f"Type: {day['content_type']}\n"
            content += f"Hook: {day['hook']}\n"
            content += f"Angle: {day['angle']}\n"
            content += f"Hashtags: {', '.join(day['hashtags'])}\n"
            content += f"CTA: {day['cta']}\n\n"
        
        content += "🧱 Monetization Blueprint\n\n"
        content += "Current Monetization Signals:\n"
        for signal, active in monetization_blueprint['current_monetization'].items():
            if active:
                content += f"- {signal.replace('_', ' ').title()}\n"
        
        content += "\nRecommended Paths:\n"
        content += "Minimum Viable:\n"
        for path in monetization_blueprint['recommended_paths']['minimum_viable']:
            content += f"- {path}\n"
        content += "\nHigh Ticket:\n"
        for path in monetization_blueprint['recommended_paths']['high_ticket']:
            content += f"- {path}\n"
        content += "\nRecurring Revenue:\n"
        for path in monetization_blueprint['recommended_paths']['recurring']:
            content += f"- {path}\n"
        
        content += "\nRevenue Model:\n"
        content += f"Lead Magnet: {monetization_blueprint['revenue_model']['lead_magnet']}\n"
        content += f"Funnel Type: {monetization_blueprint['revenue_model']['funnel_type']}\n"
        content += "Upsell Path:\n"
        for tier, offer in monetization_blueprint['revenue_model']['upsell_path'].items():
            content += f"- {tier.title()}: {offer}\n"
        content += "\nPricing Strategy:\n"
        for tier, price in monetization_blueprint['revenue_model']['pricing_strategy'].items():
            content += f"- {tier.replace('_', ' ').title()}: {price}\n"
        
        content += "\n🔁 Automation & Funnel Stack\n\n"
        content += "Recommended Tools:\n"
        content += "- CRM: ActiveCampaign or ConvertKit\n"
        content += "- Funnel Builder: ClickFunnels or Kartra\n"
        content += "- Scheduling: Buffer or Later\n"
        content += "- Analytics: Google Analytics and platform insights\n"
        content += "- Email Marketing: Automated welcome sequence\n"
        content += "- Social Media Management: Content calendar integration\n"
        
        content += "\n🎯 Immediate Opportunities\n\n"
        content += "1. Implement the viral content framework\n"
        content += "2. Set up the recommended monetization path\n"
        content += "3. Create the lead magnet and funnel\n"
        content += "4. Start the content calendar\n"
        content += "5. Set up automation workflows\n"
        
        return content

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"})

@app.post("/analyze/{client_id}")
async def analyze_client(client_id: str):
    analyzer = ContentAnalyzer()
    try:
        analyzer.analyze_niche(client_id)
        return JSONResponse(content={"status": "success", "message": f"Analysis completed for client {client_id}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 