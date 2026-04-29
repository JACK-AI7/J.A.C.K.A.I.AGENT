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
            
            err_str = str(e).lower()
            restarted = False
            if "10054" in err_str or "connection" in err_str or "timeout" in err_str:
                print("Connection to Ollama lost. Attempting to restart...")
                self._ensure_ollama_running()
                restarted = True
                
            if restarted:
                try:
                    return self._process_ollama(query)
                except Exception as retry_e:
                    print(f"Retry after restart failed: {retry_e}")
                    
            # Try falling back to a smaller model
            if self.model != "llama3.2:1b":
                print(f"Fallback: Switching to llama3.2:1b...")
                old_model = self.model
                self.model = "llama3.2:1b"
                try:
                    result = self._process_ollama(query)
                    self.model = old_model  # Restore original
                    return result
                except Exception as fallback_e:
                    print(f"Fallback Neural Error: {fallback_e}")
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
        
        # System actions → Qwen 2.5 (Best tool-calling model)
        is_action = any(word in query_lower for word in ["open", "launch", "start", "run", "click", "type", "command", "system", "search", "terminal", "press", "refresh", "reload"])
        if is_action and "qwen" in MODEL_PROFILES:
            action_model = MODEL_PROFILES["qwen"]["model"]
            print(f"TITAN Worker: Deploying '{action_model}' for reliable tool-calling...")
            get_signals().emit_bridge("thought_received", f"Neural Overdrive: Engaging Action worker ({action_model})...", "thought")
            current_model = action_model
            
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_manager.get_context_messages())
        messages.append({"role": "user", "content": query})
        
        tools = [{"type": "function", "function": f} for f in FUNCTIONS]
        
        # --- TOOL FILTERING ---
        # Reduce tool noise for smaller models by filtering based on intent
        if is_action:
            action_keywords = ["browser", "click", "type", "navigator", "system", "command", "skill", "launch", "open", "press"]
            tools = [t for t in tools if any(kw in t["function"]["name"].lower() or kw in t["function"]["description"].lower() for kw in action_keywords)]
        elif is_coding:
            coding_keywords = ["code", "file", "terminal", "python", "debug"]
            tools = [t for t in tools if any(kw in t["function"]["name"].lower() or kw in t["function"]["description"].lower() for kw in coding_keywords)]
        
        # Always include auto_navigator and youtube_master for general missions
        if is_action or is_reasoning:
            important_tools = ["auto_navigator", "youtube_master", "open_any_url", "open_youtube"]
            for tool_name in important_tools:
                if not any(t["function"]["name"] == tool_name for t in tools):
                    match = next((f for f in FUNCTIONS if f["name"] == tool_name), None)
                    if match: tools.append({"type": "function", "function": match})
        
        try:
            response = self.ollama_client.chat(model=current_model, messages=messages, tools=tools, options=self.profile["options"])
        except:
            response = self.ollama_client.chat(model=current_model, messages=messages, options=self.profile["options"])
            
        msg = response.get("message", {})
        tool_results = []
        content = msg.get("content", "")

        # 1. Handle API Tool Calls
        if msg.get("tool_calls"):
            for tc in msg["tool_calls"]:
                name = tc["function"]["name"]
                args = tc["function"]["arguments"]
                res = self._execute_function(name, args)
                tool_results.append({"function": name, "args": args, "result": res})
        
        # 2. Handle Inline Tool Calls (Fallback for smaller/unreliable models)
        inline_tools = self._parse_inline_tool_calls(content)
        for it in inline_tools:
            name = it.get("name") or it.get("function")
            args = it.get("arguments") or it.get("args") or {}
            if name and name not in [tr["function"] for tr in tool_results]:
                res = self._execute_function(name, args)
                tool_results.append({"function": name, "args": args, "result": res})

        # 3. Final Content Determination
        if tool_results:
            # ALWAYS do a second pass for natural language response after execution
            # This ensures the model confirms what it did instead of showing JSON/technical text.
            try:
                # Prepare context for the model to describe what it did
                tool_resp_str = "\n".join([f"Tool '{tr['function']}' result: {tr['result']}" for tr in tool_results])
                
                # Create a fresh conversation segment for the confirmation
                confirmation_messages = [{"role": "system", "content": "You are JACK. A tool has just been executed. Provide a brief, professional, and natural confirmation to the user (e.g., 'I have opened YouTube for you, Sir'). Do NOT mention the tool name or technical details."}]
                confirmation_messages.append({"role": "user", "content": f"Query: {query}\n\n{tool_resp_str}"})
                
                final_response = self.ollama_client.chat(model=current_model, messages=confirmation_messages, options=self.profile["options"])
                content = final_response.get("message", {}).get("content", content)
            except Exception as e:
                print(f"Confirmation Error: {e}")
                if not content:
                    content = "The mission parameters have been executed, Sir."
        
        res = self._sanitize_persona_output(content)
        self.conversation_manager.add_interaction(query, res, tool_results)
        return res

    def _parse_inline_tool_calls(self, text):
        """Extract tool calls from raw text using regex (JSON, code blocks, identifiers, etc.)."""
        if not text: return []
        found = []
        
        # 1. Look for JSON-like blocks { ... }
        potential_blocks = re.findall(r"\{[^{}]+\}", text)
        for block in potential_blocks:
            try:
                clean_block = re.sub(r"<nil>", "null", block)
                data = json.loads(clean_block)
                if isinstance(data, dict):
                    name = data.get("name") or data.get("function") or data.get("action")
                    if name:
                        found.append({"name": name, "args": data.get("args") or data.get("arguments") or data.get("parameters") or {}})
            except:
                name_match = re.search(r"\"(?:name|function|action)\":\s*\"([^\"]+)\"", block)
                if name_match:
                    found.append({"name": name_match.group(1)})
        
        # 2. Look for command-style calls: tool_name(args) or tool_name key="value"
        # Check against known tool names
        for tool_name in FUNCTION_MAP.keys():
            # tool_name(key="value")
            call_match = re.search(rf"{tool_name}\(([^)]*)\)", text)
            if call_match:
                found.append({"name": tool_name, "args": call_match.group(1)})
                continue
                
            # tool_name key="value" or tool_name task="value"
            kv_match = re.search(rf"{tool_name}\s+(\w+)=[\"\']([^\"\']+)[\"\']", text)
            if kv_match:
                found.append({"name": tool_name, "args": {kv_match.group(1): kv_match.group(2)}})
                continue

        # 3. Look for tool names in backticks: `tool_name` or ``` tool_name ```
        code_matches = re.findall(r"`+([\w_]+)`+", text)
        for cb in code_matches:
            if cb in FUNCTION_MAP:
                found.append({"name": cb})
                
        # 4. Look for "execute tool_name" or "call tool_name"
        for tool_name in FUNCTION_MAP.keys():
            if f"execute {tool_name}" in text.lower() or f"call {tool_name}" in text.lower():
                found.append({"name": tool_name})
                
        return found

    def _execute_function(self, name, args):
        """Safe tool execution bridge."""
        if name in FUNCTION_MAP:
            try:
                print(f"TITAN EXEC: {name}({args})")
                get_signals().emit_bridge("tool_log", f"RUNNING: {name}")
                
                # Normalize args
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        pass
                
                # Execute
                func = FUNCTION_MAP[name]
                if isinstance(args, dict):
                    # Filter args to only those accepted by the function if needed
                    # For now, just pass them
                    return str(func(**args))
                else:
                    # Single argument or no arguments
                    try:
                        return str(func(args))
                    except TypeError:
                        return str(func())
            except Exception as e:
                return f"Execution Error: {str(e)}"
        return f"Neural Error: Tool '{name}' is not in my database."

    def _sanitize_persona_output(self, text):
        if not text: return "Action completed, Sir."
        
        # Remove reasoning tags
        text = re.sub(r"<(thought|reasoning|reflection|thought_process)>.*?</\1>", "", text, flags=re.DOTALL)
        
        # Remove code blocks containing only a tool name or simple identifier
        text = re.sub(r"`+[\w_]+`+", "", text)
        
        # Remove JSON-like blocks that look like tool calls or descriptions
        # We catch blocks containing "name", "function", "args", or "description"
        text = re.sub(r"\{[^{}]*\"(?:name|function|args|arguments|description|parameters)\"[^{}]*\}", "", text)
        
        # Remove weird Ollama internal structures sometimes leaked: {function <nil> ...}
        text = re.sub(r"\{function <nil>.*?\}", "", text)
        
        # Clean up whitespace
        text = re.sub(r"\s+", " ", text).strip()
        
        # If the text is just common filler after sanitization, or empty
        if not text or text.lower() in ["here is the function:", "possible completion:", "you want to:"]:
            return "Task accomplished, Sir."
        
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
