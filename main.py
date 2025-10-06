from extractor import StartupCommentAnalyzer

def main():
    analyzer = StartupCommentAnalyzer()
    
    try:
        subreddit = analyzer.reddit.subreddit('startups')
        print(f"✅ Connected to r/{subreddit.display_name}")
        
        post_url = "https://www.reddit.com/r/startups/comments/1lxc97s/share_your_startup_quarterly_post/"
        print("🚀 Starting comment scraping and analysis...")
        analyzer.scrape_startup_comments(post_url, limit_comments=15)
        
        print("\n📊 EXTRACTED STARTUPS\n")
        startups = analyzer.query_startups("""
            SELECT startup_name, location, company_url, description 
            FROM startups 
            ORDER BY startup_name
        """)
        
        for i, startup in enumerate(startups, 1):
            name, location, url, desc = startup
            print(f"\n{i}. 🏢 {name or 'Unnamed Startup'}")
            print(f"   📍 Location: {location or 'Not specified'}")
            print(f"   🌐 URL: {url or 'No website'}")
            print(f"   📝 Description: {desc or 'No description'}")
            print("-" * 50)
        
        print(f"\n✅ Total startups extracted: {len(startups)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
