import os
from firecrawl import FirecrawlApp

def execute(url=None, task="scrape"):
    """
    TITAN Action: Deep Web Extraction via Firecrawl.
    Actions: 'scrape', 'crawl', 'map'.
    """
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return "Skill Error: FIRECRAWL_API_KEY is missing from .env."

    app = FirecrawlApp(api_key=api_key)

    try:
        if task == "scrape":
            print(f"Firecrawl: Scraping {url}...")
            result = app.scrape_url(url, params={'formats': ['markdown']})
            return f"Scrape Success:\n{result.get('markdown', 'No content found.')[:2000]}..."
            
        elif task == "crawl":
            print(f"Firecrawl: Initiating deep crawl of {url}...")
            crawl_status = app.crawl_url(url, params={'limit': 10, 'scrapeOptions': {'formats': ['markdown']}})
            return f"Crawl Initiated. ID: {crawl_status.get('id')}"
            
        elif task == "map":
            print(f"Firecrawl: Mapping infrastructure of {url}...")
            map_result = app.map_url(url)
            return f"Site Map: {map_result}"
            
        return "Invalid action. Use 'scrape', 'crawl', or 'map'."
    except Exception as e:
        return f"Firecrawl Error: {str(e)}"
