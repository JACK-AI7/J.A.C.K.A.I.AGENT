import json
import ollama
import random
import time
import re
import os
import subprocess
import urllib.request
import google.generativeai as genai
from groq import Groq

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
    def __init__(self, hud=None):
        self.hud = hud
        self.profile = MODEL_PROFILES.get(ACTIVE_PROFILE, MODEL_PROFILES["qwen"])
        self.provider = self.profile.get("provider", "ollama")
        self.model = self.profile["model"]
        self.conversation_manager = ConversationManager()
        
        # Initialize Clients
        self._init_clients()
        self.reasoning_mode = True  # Enable OpenJarvis style reflective thinking

    def _init_clients(self):
        """Lazy-init the required provider client with validation."""
        if self.provider == "google":
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key and "your_" not in api_key:
                genai.configure(api_key=api_key)
                # Define tools for Gemini
                gemini_tools = [self._map_to_google_tool(f) for f in FUNCTIONS]
                self.google_model = genai.GenerativeModel(
                    self.model,
                    tools=[dict(function_declarations=gemini_tools)]
                )
            else:
                print("Gemini API Key missing/invalid. Falling back to Ollama.")
                self.provider = "ollama"
        
        if self.provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if api_key and "your_" not in api_key:
                self.groq_client = Groq(api_key=api_key)
            else:
                print("Groq API Key missing/invalid. Falling back to Ollama.")
                self.provider = "ollama"

        if self.provider == "ollama":
            self._ensure_ollama_running()
            self.ollama_client = ollama.Client(host=OLLAMA_SETTINGS["base_url"], timeout=30.0)

    def _map_to_google_tool(self, f):
        """Convert standard tool spec to Google Generative AI format."""
        return {
            "name": f["name"],
            "description": f["description"],
            "parameters": f["parameters"]
        }

    def _ensure_ollama_running(self):
        try:
            urllib.request.urlopen(OLLAMA_SETTINGS["base_url"], timeout=2)
        except Exception:
            try:
                subprocess.Popen("ollama serve", shell=True, 
                                 creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
                time.sleep(3)
            except: pass

    def process_query(self, query):
        """The main brain entry point. Routes to Gemini, Groq, or Ollama."""
        query = self._normalize_input(query)
        
        # System Command Bypass
        bypass = self._check_bypass_commands(query)
        if bypass: return bypass

        try:
            print(f"Thinking ({self.provider.upper()}: {self.model})...")
            get_signals().emit_bridge("thought_received", f"Neural Synthesis: Engaging {self.model} via {self.provider}...", "thought")
            get_signals().emit_bridge("neural_pulse", 10)

            if self.provider == "google":
                return self._process_google(query)
            elif self.provider == "groq":
                return self._process_groq(query)
            else:
                return self._process_ollama(query)

        except Exception as e:
            print(f"Neural Error in {self.provider}: {e}")
            if self.provider != "ollama":
                print("Automatic Fallback to local Ollama...")
                self.provider = "ollama"
                self._init_clients()
                return self.process_query(query)
            return f"Neural Interface Error: {str(e)}"

    def _process_google(self, query):
        """Handle reasoning via Google Gemini API."""
        chat = self.google_model.start_chat(history=self._get_google_history())
        response = chat.send_message(query)
        
        final_text = ""
        tool_results = []

        # Gemini might return content or tool calls
        for part in response.parts:
            if part.text:
                final_text += part.text
            if part.function_call:
                fn_name = part.function_call.name
                fn_args = dict(part.function_call.args)
                
                print(f"GEMINI CALLING: {fn_name}({fn_args})")
                get_signals().emit_bridge("pipeline_stage", "ACTING", f"Tool: {fn_name}")
                
                result = self._execute_function(fn_name, fn_args)
                tool_results.append({"function": fn_name, "args": fn_args, "result": result})
                
                # Push tool result back to Gemini for final synthesis
                response = chat.send_message(
                    genai.types.Content(
                        parts=[genai.types.Part.from_function_response(
                            name=fn_name,
                            response={'result': str(result)}
                        )]
                    )
                )
                if response.text:
                    final_text = response.text

        res = self._sanitize_persona_output(final_text)
        self.conversation_manager.add_interaction(query, res, tool_results)
        return res

    def _process_groq(self, query):
        """Ultra-fast reasoning via Groq API."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_manager.get_context_messages())
        messages.append({"role": "user", "content": query})

        tools = [{"type": "function", "function": f} for f in FUNCTIONS]
        
        response = self.groq_client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=self.profile["options"].get("temperature", 0.7)
        )

        msg = response.choices[0].message
        tool_results = []
        
        if msg.tool_calls:
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                
                get_signals().emit_bridge("pipeline_stage", "ACTING", f"Tool: {fn_name}")
                result = self._execute_function(fn_name, fn_args)
                tool_results.append({"function": fn_name, "args": fn_args, "result": result})
            
            # Simple synthesis for Groq
            content = "Action synchronized, Sir."
            # Only summarize if it's an information tool
            if any(name.startswith("get") or "search" in name for name in [tc.function.name for tc in msg.tool_calls]):
                # Add tool results to context and call again for summary
                messages.append(msg)
                for i, tc in enumerate(msg.tool_calls):
                    messages.append({
                        "tool_call_id": tc.id,
                        "role": "tool",
                        "name": tool_results[i]["function"],
                        "content": str(tool_results[i]["result"])
                    })
                final_res = self.groq_client.chat.completions.create(model=self.model, messages=messages)
                content = final_res.choices[0].message.content
        else:
            content = msg.content or "Processing complete."

        res = self._sanitize_persona_output(content)
        self.conversation_manager.add_interaction(query, res, tool_results)
        return res

    def _process_ollama(self, query):
        """Ollama local reasoning (Original flow with improved stability)."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self.conversation_manager.get_context_messages())
        messages.append({"role": "user", "content": query})
        
        tools = [{"type": "function", "function": f} for f in FUNCTIONS]
        
        try:
            response = self.ollama_client.chat(model=self.model, messages=messages, tools=tools, options=self.profile["options"])
        except:
            response = self.ollama_client.chat(model=self.model, messages=messages, options=self.profile["options"])
            
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

    def _get_google_history(self):
        history = []
        for msg in self.conversation_manager.get_context_messages():
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        return history

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
