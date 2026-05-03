import asyncio
import re
from core.config import SEARCH_SETTINGS
from core.nexus_bridge import get_signals

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
        
        # Simple extraction of top 3 URLs from snippets
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', snippets)[:3]
        
        if not urls:
            signals.thought_received.emit("No seed URLs found. Falling back to snippet analysis.", "decision")
            return f"Deep Search: No reliable URLs found in snippets. Fallback data:\n{snippets}"
        
        if not CRAWL4AI_AVAILABLE:
            signals.thought_received.emit("Crawl4AI not detected. Performance degraded.", "log")
            return f"Deep Search: crawl4ai not installed. Snippet results:\n{snippets}"
            
        signals.node_added.emit("search_root", f"Search: {query}", "search", None)
        signals.thought_received.emit(f"Engaging Multi-Hop Crawl on top {len(urls)} sources", "decision")
        
        all_content = []
        async with AsyncWebCrawler() as crawler:
            for i, target_url in enumerate(urls):
                signals.node_added.emit(f"url_{i}", f"Source {i+1}: {target_url}", "url", "search_root")
                signals.status_updated.emit("Deep Search", 30 + (i*20), f"url_{i}")
                
                try:
                    result = await crawler.arun(url=target_url)
                    if result.success:
                        content = result.markdown_v2.raw_markdown if hasattr(result, 'markdown_v2') else str(result)
                        all_content.append(f"--- SOURCE {i+1}: {target_url} ---\n{content[:3000]}")
                        signals.thought_received.emit(f"Source {i+1} capture successful.", "thought")
                    else:
                        signals.thought_received.emit(f"Source {i+1} failed.", "log")
                except Exception:
                    continue
        
        if not all_content:
            return f"Deep Search: Extraction failed for all candidate URLs. Fallback:\n{snippets}"
            
        full_report = "\n\n".join(all_content)
        signals.status_updated.emit("Deep Search", 100, "search_root")
        return f"ULTIMATE RESEARCH GATHERED ({len(urls)} sources):\n\n{full_report}"


# Singleton Search Agent
search_agent = DeepSearchAgent()

SEARCH_AVAILABLE = True  # Always available (falls back to snippets)

async def deep_search_mission(query):
    """Bridge for the toolset."""
    return await search_agent.intensive_search(query)
