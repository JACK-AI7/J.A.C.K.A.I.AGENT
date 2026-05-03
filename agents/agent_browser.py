import os
import asyncio
import shutil
import tempfile
import psutil
try:
    from browser_use import Agent, Browser
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    Agent = None
    Browser = None
    print("TITAN Browser: Engine 'browser-use' still installing...")

try:
    from langchain_ollama import ChatOllama
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    ChatOllama = None
    print("TITAN AI: Engine 'langchain-ollama' still installing...")
from core.config import OLLAMA_SETTINGS
from core.nexus_bridge import get_signals

# Path to real Chrome User Data identified earlier
CHROME_USER_DATA = os.path.expandvars('%LOCALAPPDATA%\\Google\\Chrome\\User Data')

class TitanBrowser:
    """The 'Immortal' Browser Agent using Browser-Use and real Chrome profile."""
    
    def __init__(self):
        if not LANGCHAIN_AVAILABLE or ChatOllama is None:
            self.llm = None
            return
            
        # Using Mistral (7B) natively via Ollama for superior Browser reasoning
        raw_llm = ChatOllama(
            model="mistral:latest", 
            base_url="http://localhost:11434"
        )
        
        # We wrap the LLM because browser-use 0.12.6 tries to monkeypatch the LLM
        # which fails on strict Pydantic models like ChatOllama.
        class LLMWrapper:
            def __init__(self, llm):
                self.executor = llm
                self.provider = "ollama"
                self.model_name = getattr(llm, "model", "mistral")
            def __getattr__(self, name):
                return getattr(self.executor, name)
            def invoke(self, *args, **kwargs):
                return self.executor.invoke(*args, **kwargs)
            async def ainvoke(self, *args, **kwargs):
                return await self.executor.ainvoke(*args, **kwargs)
                
        self.llm = LLMWrapper(raw_llm)

    def _get_target_path(self):
        """Determine the browser profile path, using Ghost Clone if Chrome is active."""
        if not BROWSER_USE_AVAILABLE:
            return None
            
        target_path = CHROME_USER_DATA
        
        # Check if Chrome is running and likely locking the profile
        chrome_running = any("chrome" in p.name().lower() for p in psutil.process_iter())
        
        if chrome_running:
            print("TITAN Browser: Chrome is active. Initiating Ghost Clone...")
            temp_profile = os.path.join(tempfile.gettempdir(), 'jack_ghost_profile')
            
            try:
                if os.path.exists(temp_profile):
                    shutil.rmtree(temp_profile, ignore_errors=True)
                os.makedirs(temp_profile, exist_ok=True)
                target_path = temp_profile
            except Exception as e:
                print(f"TITAN Browser: Ghost Clone failed ({e}), attempting direct access.")

        return target_path

    async def run_task(self, task_description):
        """Execute a high-level browsing task with the user's logged-in Chrome profile."""
        if not BROWSER_USE_AVAILABLE:
            return "Titan Browser: Engine unavailable. Run 'pip install browser-use' to activate."
            
        signals = get_signals()
        signals.thought_received.emit(f"Engaging Web Agent for mission: {task_description[:50]}...", "decision")
        signals.node_added.emit("browser_root", f"Browser Mission: {task_description[:30]}", "search", None)
        signals.status_updated.emit("Web Agent", 20, "browser_root")

        profile_path = self._get_target_path()
        browser = Browser(headless=False, user_data_dir=profile_path)
        agent = Agent(
            task=task_description,
            llm=self.llm,
            browser=browser
        )
        
        print(f"Titan Browser: Starting task - {task_description}")
        try:
            signals.thought_received.emit("Calibrating DOM and navigating...", "thought")
            result = await agent.run()
            signals.thought_received.emit("Browser Mission Successful.", "thought")
            signals.status_updated.emit("Web Agent", 100, "browser_root")
            await browser.stop()
            return result
        except Exception as e:
            signals.thought_received.emit(f"Browser Interruption: {str(e)}", "log")
            try:
                await browser.stop()
            except: pass
            raise e

def browse_titan(query):
    """Sync wrapper for the async Titan Browser."""
    # We'll use a new event loop for this call
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(TitanBrowser().run_task(query))
        return str(result)
    except Exception as e:
        return f"Titan Browser Error: {str(e)}"

if __name__ == "__main__":
    # Test
    print(browse_titan("Check my YouTube notifications and tell me the latest one."))
