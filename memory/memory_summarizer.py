import asyncio
import time
from core.logger import log_event
from memory.persistent_memory import persistent_memory

class MemorySummarizer:
    """Background engine that condenses and organizes long-term memories."""
    
    def __init__(self, ai_handler):
        self.ai = ai_handler
        self.is_running = False

    async def start(self):
        """Periodically summarize recent interactions."""
        self.is_running = True
        log_event("MEMORY_SUMMARIZER: Neural cleanup engine online.")
        while self.is_running:
            # Run every hour (simulated shorter for testing if needed)
            await asyncio.sleep(3600) 
            
            try:
                log_event("MEMORY_SUMMARIZER: Starting periodic summarization...")
                recent = persistent_memory.get_recent(limit=20)
                if len(recent) < 5: continue # Wait for more content
                
                context = "\n".join([f"[{m['timestamp']}] {m['content']}" for m in recent])
                prompt = f"""
                Summarize the following recent agent interactions into 3-5 key takeaways for long-term storage.
                Focus on user preferences, completed tasks, and recurring themes.
                
                INTERACTIONS:
                {context}
                
                Summary:
                """
                
                summary = self.ai.generate([{"role": "user", "content": prompt}])
                # Store the summary as a new high-level memory
                persistent_memory.add_memory(summary, memory_type="long_term_summary")
                log_event("MEMORY_SUMMARIZER: Cleanup complete. Knowledge condensed.")
                
            except Exception as e:
                log_event(f"MEMORY_SUMMARIZER: Error: {e}")
