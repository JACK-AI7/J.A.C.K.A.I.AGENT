import json
import ollama
import random
import time
import re
import os
import subprocess
import urllib.request

try:
    from nexus_bridge import get_signals
except Exception:
    class _DummySignals:
        def emit_bridge(self, *a, **kw): pass
    _dummy = _DummySignals()
    def get_signals(): return _dummy

from config import OLLAMA_SETTINGS, SYSTEM_PROMPT, MODEL_PROFILES, ACTIVE_PROFILE
from tools import FUNCTIONS, FUNCTION_MAP
from conversation_manager import ConversationManager


class AIHandler:
    """100% FREE & OPEN-SOURCE AI Handler — runs exclusively on local Ollama models."""
    
    def __init__(self, hud=None):
        self.hud = hud
        self.profile = MODEL_PROFILES.get(ACTIVE_PROFILE, MODEL_PROFILES["reasoning"])
        self.provider = "ollama"  # ALWAYS local — no paid APIs
        self.model = self.profile["model"]
        self.conversation_manager = ConversationManager()
        
        # Initialize Ollama client
        self._init_clients()
        self.reasoning_mode = True  # Enable reflective thinking

    def _init_clients(self):
        """Initialize local Ollama client. No paid API keys needed."""
        self._ensure_ollama_running()
        self.ollama_client = ollama.Client(host=OLLAMA_SETTINGS["base_url"], timeout=120.0)
        
        # Emit model status
        try:
            get_signals().emit_bridge("model_active", "OLLAMA", f"{self.model.upper()} (100% FREE)")
        except: pass

    def _ensure_ollama_running(self):
        """Checks if Ollama is running, starts it if not, and waits for readiness."""
        for attempt in range(5):
            try:
                urllib.request.urlopen(OLLAMA_SETTINGS["base_url"], timeout=2)
                return True
            except Exception:
                if attempt == 0:
                    try:
                        subprocess.Popen("ollama serve", shell=True, 
                                         creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
                    except: pass
                time.sleep(2)
        return False

    def process_query(self, query):
        """The main brain entry point. Routes to local Ollama models ONLY."""
        query = self._normalize_input(query)
        
        # System Command Bypass
        bypass = self._check_bypass_commands(query)
        if bypass: return bypass

        try:
            print(f"Thinking (OLLAMA: {self.model})...")
            get_signals().emit_bridge("thought_received", f"Neural Synthesis: Engaging {self.model} (FREE/LOCAL)...", "thought")
            get_signals().emit_bridge("neural_pulse", 10)

            return self._process_ollama(query)

        except Exception as e:
            print(f"Neural Error: {e}")
            # Try falling back to a smaller model
            if self.model != "llama3.2:1b":
                print(f"Fallback: Switching to llama3.2:1b...")
                old_model = self.model
                self.model = "llama3.2:1b"
                try:
                    result = self._process_ollama(query)
                    self.model = old_model  # Restore original
                    return result
                except:
                    self.model = old_model
            return f"Neural Interface Error: {str(e)}"

    def _process_ollama(self, query):
        """Ollama local reasoning with dynamic worker delegation."""
        current_model = self.model
        
        # --- DYNAMIC WORKER DELEGATION ---
        query_lower = query.lower()
        
        # Code tasks → Qwen2.5-Coder
        is_coding = any(word in query_lower for word in ["code", "script", "program", "python", "javascript", "debug", "write a", "technical", "fix the", "implement"])
        if is_coding and "coder" in MODEL_PROFILES:
            coder_model = MODEL_PROFILES["coder"]["model"]
            print(f"TITAN Worker: Deploying '{coder_model}' for high-accuracy engineering...")
            get_signals().emit_bridge("thought_received", f"Neural Handshake: Engaging Coder worker ({coder_model})...", "thought")
            current_model = coder_model
        
        # Deep reasoning → Use reasoning model explicitly
        is_reasoning = any(word in query_lower for word in ["explain", "analyze", "think about", "why", "compare", "evaluate", "reason"])
        if is_reasoning and "reasoning" in MODEL_PROFILES:
            current_model = MODEL_PROFILES["reasoning"]["model"]
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_manager.get_context_messages())
        messages.append({"role": "user", "content": query})
        
        tools = [{"type": "function", "function": f} for f in FUNCTIONS]
        
        try:
            response = self.ollama_client.chat(model=current_model, messages=messages, tools=tools, options=self.profile["options"])
        except:
            response = self.ollama_client.chat(model=current_model, messages=messages, options=self.profile["options"])
            
        msg = response.get("message", {})
        tool_results = []
        content = msg.get("content", "")

        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                name = tc["function"]["name"]
                args = tc["function"]["arguments"]
                res = self._execute_function(name, args)
                tool_results.append({"function": name, "args": args, "result": res})
            content = content or "The mission parameters have been executed."

        res = self._sanitize_persona_output(content)
        self.conversation_manager.add_interaction(query, res, tool_results)
        return res

    def _execute_function(self, name, args):
        """Safe tool execution bridge."""
        if name in FUNCTION_MAP:
            try:
                print(f"TITAN EXEC: {name}({args})")
                get_signals().emit_bridge("tool_log", f"RUNNING: {name}")
                
                # Some models pass args as string, some as dict
                if isinstance(args, str):
                    args = json.loads(args)
                
                return str(FUNCTION_MAP[name](**args))
            except Exception as e:
                return f"Execution Error: {str(e)}"
        return f"Neural Error: Tool '{name}' is not in my database."

    def _sanitize_persona_output(self, text):
        if not text: return "Action completed, Sir."
        # Keep reasoning tags if they are useful, but JACK usually hides them
        if "<thought>" in text and "</thought>" in text:
             thought = re.search(r"<thought>(.*?)</thought>", text, re.DOTALL)
             if thought:
                 print(f"TITAN Internal Reasoning: {thought.group(1).strip()[:200]}...")
        
        text = re.sub(r"<(thought|reasoning)>.*?</\1>", "", text, flags=re.DOTALL)
        text = re.sub(r"\{'function':.*?\}", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _normalize_input(self, query):
        if not query: return ""
        q_low = query.lower()
        if "ya shour" in q_low or "ya shock" in q_low: query = "yes sure"
        return query

    def _check_bypass_commands(self, query):
        q = query.lower()
        if "restart" in q and "jack" in q:
            from skills.system_doctor.action import execute as restart
            restart("reload")
            return "Rebirthing system cores now. See you on the other side, Sir."
        if "dashboard" in q or "nexus" in q:
            if self.hud and hasattr(self.hud, "launch_nexus_dashboard"):
                self.hud.launch_nexus_dashboard()
                return "Connecting visualization grid. Nexus Dashboard Online."
        return None

    def clear_conversation_history(self):
        """Clear conversation history."""
        self.conversation_manager.clear_history()
        return "Neural memory purged, Sir. Starting fresh."

    def switch_model(self, profile_name):
        """Switch to a different model profile."""
        if profile_name in MODEL_PROFILES:
            self.profile = MODEL_PROFILES[profile_name]
            self.model = self.profile["model"]
            get_signals().emit_bridge("model_active", "OLLAMA", f"{self.model.upper()} (FREE)")
            return f"Switched to {profile_name}: {self.model}"
        return f"Unknown profile: {profile_name}. Available: {', '.join(MODEL_PROFILES.keys())}"
