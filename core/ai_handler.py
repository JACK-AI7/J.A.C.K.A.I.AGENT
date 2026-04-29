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
import subprocess


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

    def generate(self, prompt):
        """Standard generation method for Production Core (Executor compatibility)."""
        from config import FALLBACK_PROFILE
        
        # Build messages with system prompt for strict JSON enforcement
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # 1. Main Mission: High-performance client with strict JSON formatting
            response = self.ollama_client.chat(
                model=self.model, 
                messages=messages, 
                format='json',
                options=self.profile.get("options", {})
            )
            return response.get("message", {}).get("content", "").strip()
        except Exception as e:
            # 2. Fallback Protocol: Reliability override
            try:
                fallback_model = MODEL_PROFILES[FALLBACK_PROFILE]["model"]
                print(f"TITAN LOG: High-performance core offline. Deploying Fallback ({fallback_model})...")
                response = self.ollama_client.chat(
                    model=fallback_model, 
                    messages=messages,
                    format='json'
                )
                return response.get("message", {}).get("content", "").strip()
            except:
                # 3. Emergency Bypass: Subprocess
                response = subprocess.run(
                    ["ollama", "run", self.model, "--format", "json"],
                    input=prompt,
                    text=True,
                    capture_output=True
                )
                return response.stdout.strip()

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
        """Strict JSON autonomous loop — upgraded for high-performance tool execution."""
        from config import AUTONOMOUS_SETTINGS, MODEL_PROFILES
        from memory_vault import vault
        
        max_depth = AUTONOMOUS_SETTINGS.get("max_tool_calls", 25)
        current_model = self.model
        
        # --- MARKET-READY LOGGING ---
        print(f"TITAN LOG: Mission started - '{query}'")
        get_signals().emit_bridge("thought_received", f"Initializing Mission Protocol: {query}", "thought")

        # --- MEMORY RECALL ---
        relevant_facts = vault.retrieve_relevant_facts(query, limit=3)
        context_facts = "\n".join([f"- {f}" for f in relevant_facts])
        
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context_facts:
            messages.append({"role": "system", "content": f"Neural Archive Context:\n{context_facts}"})
            
        messages.extend(self.conversation_manager.get_context_messages())
        messages.append({"role": "user", "content": f"Task: {query}"})
        
        tool_results_summary = []
        
        for step in range(max_depth):
            print(f"TITAN LOG: Executing Mission Step {step+1}/{max_depth}...")
            get_signals().emit_bridge("neural_pulse", 20 + (step * 5))
            
            data = None
            # --- GENERATION RETRY MECHANISM ---
            for attempt in range(2):
                try:
                    response = self.ollama_client.chat(
                        model=current_model, 
                        messages=messages, 
                        format='json', 
                        options=self.profile.get("options", {})
                    )
                    
                    raw_content = response.get("message", {}).get("content", "")
                    if not raw_content:
                        continue
                    
                    # --- JSON VALIDATOR ---
                    data = self._parse_json_robustly(raw_content)
                    if data and data.get("type") in ["tool", "final"]:
                        break # Successful parse
                except Exception as e:
                    print(f"TITAN LOG: Generation Attempt {attempt+1} failed: {e}")
                    time.sleep(1)
            
            if not data:
                return "Neural Error: Failed to generate valid JSON command after retries."

            res_type = data.get("type")
            
            if res_type == "tool":
                tool_name = data.get("name")
                tool_args = data.get("args") or {}
                
                # --- EXECUTION QUEUE LOGGING ---
                print(f"TITAN LOG: Step {step+1} - Calling Tool: {tool_name}")
                get_signals().emit_bridge("tool_log", f"EXECUTING: {tool_name}")
                
                result = self._execute_function(tool_name, tool_args)
                
                tool_results_summary.append({"function": tool_name, "args": tool_args, "result": result})
                
                messages.append({"role": "assistant", "content": json.dumps(data)})
                messages.append({"role": "user", "content": f"Result: {result}"})
                
                get_signals().emit_bridge("thought_received", f"Step {step+1} Complete: {tool_name} returned data.", "decision")
                
            elif res_type == "final":
                final_msg = data.get("message", "Task completed.")
                status = data.get("status", "success")
                
                # --- MEMORY STORAGE ---
                if status == "success":
                    vault.store_fact(f"User Task: {query} | Result: {final_msg}")
                
                print(f"TITAN LOG: Mission Finalized - Status: {status}")
                self.conversation_manager.add_interaction(query, final_msg, tool_results_summary)
                return final_msg
            
            else:
                messages.append({"role": "user", "content": "Error: Your response must follow the strict JSON format (type: tool | final)."})

        return "Mission Termination: Maximum depth reached."

    def _parse_json_robustly(self, text):
        """High-tech JSON validator/parser."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract from potential markdown/clutter
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except: pass
        return None

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
