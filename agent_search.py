import asyncio
import re
from config import SEARCH_SETTINGS
from nexus_bridge import get_signals

# Safe import — crawl4ai may not be installed
try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    AsyncWebCrawler = None
    print("TITAN Search: crawl4ai not installed. Deep crawling disabled. Run: pip install crawl4ai")


class DeepSearchAgent:
    """The 'Immortal' Searcher: Uses Crawl4AI to read entire pages for perfect accuracy."""
    
    def __init__(self):
        self.crawler = None

    async def intensive_search(self, query):
        """Perform a deep search and return summarized markdown data."""
        signals = get_signals()
        signals.thought_received.emit(f"Initializing Deep Search for: {query}", "thought")
        signals.status_updated.emit("Deep Search", 10, "search_initial")
        
        # 1. First get snippets to find the best URL
        from tools import get_web_data
        signals.thought_received.emit("Quering DuckDuckGo for candidate seeds...", "thought")
        snippets = get_web_data(query)
        
        # Simple extraction of first URL from snippets
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', snippets)
        
        if not urls:
            signals.thought_received.emit("No seed URLs found. Falling back to snippet analysis.", "decision")
            return f"Deep Search: No reliable URLs found in snippets. Fallback data:\n{snippets}"
        
        if not CRAWL4AI_AVAILABLE:
            signals.thought_received.emit("Crawl4AI not detected. Performance degraded.", "log")
            return f"Deep Search: crawl4ai not installed. Snippet results:\n{snippets}"
            
        target_url = urls[0]
        signals.node_added.emit("search_root", f"Search: {query}", "search", None)
        signals.node_added.emit("target_url", f"Target: {target_url}", "url", "search_root")
        signals.thought_received.emit(f"Engaging Crawl4AI on {target_url}", "decision")
        signals.status_updated.emit("Deep Search", 40, "target_url")
        
        try:
            async with AsyncWebCrawler() as crawler:
                signals.status_updated.emit("Deep Search", 60, "target_url")
                result = await crawler.arun(url=target_url)
                
                # 2. Extract clean markdown
                if result.success:
                    content = result.markdown_v2.raw_markdown if hasattr(result, 'markdown_v2') else str(result)
                    signals.thought_received.emit(f"Extraction successful: {len(content)} raw bytes captured.", "thought")
                    signals.status_updated.emit("Deep Search", 90, "target_url")
                    
                    # Truncate for LLM context safety
                    summary = content[:5000] if len(content) > 5000 else content
                    signals.status_updated.emit("Deep Search", 100, "target_url")
                    return f"SOURCE: {target_url}\n\nCONTENT:\n{summary}"
                else:
                    error = result.error_message if hasattr(result, 'error_message') else 'Unknown error'
                    signals.thought_received.emit(f"Crawl failed: {error}", "decision")
                    return f"Deep Search: Failed to crawl {target_url}. Error: {error}"
        except Exception as e:
            signals.thought_received.emit(f"Neural interrupt: {str(e)}", "log")
            return f"Deep Search: Crawl error ({e}). Snippet results:\n{snippets}"


# Singleton Search Agent
search_agent = DeepSearchAgent()

SEARCH_AVAILABLE = True  # Always available (falls back to snippets)

async def deep_search_mission(query):
    """Bridge for the toolset."""
    return await search_agent.intensive_search(query)
