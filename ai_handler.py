import json
import ollama
import random
import time
import re
import subprocess
import urllib.request
try:
    from nexus_bridge import get_signals
except Exception:
    class _DummySignals:
        def emit_bridge(self, *a, **kw): pass
    _dummy = _DummySignals()
    def get_signals(): return _dummy
from config import OLLAMA_SETTINGS, SYSTEM_PROMPT
from tools import FUNCTIONS, FUNCTION_MAP
from conversation_manager import ConversationManager


def _get_message(response):
    """Extract message from ollama response (handles both dict and object formats)."""
    if isinstance(response, dict):
        return response.get("message", {})
    elif hasattr(response, "message"):
        msg = response.message
        # Convert object to dict-like access
        if hasattr(msg, "content"):
            result = {
                "content": msg.content or "",
                "tool_calls": getattr(msg, "tool_calls", None),
            }
            return result
        return msg if isinstance(msg, dict) else {"content": str(msg)}
    return {"content": str(response)}


class AIHandler:
    def __init__(self, hud=None):
        self.hud = hud  # Set hud FIRST so _ensure_ollama_running can use it safely
        self._ensure_ollama_running()
        # Set a timeout for service calls to prevent hangs
        self.client = ollama.Client(
            host=OLLAMA_SETTINGS["base_url"],
            timeout=30.0,  # 30 second timeout per call
        )
        self.profile = OLLAMA_SETTINGS["current"]
        self.model = self._resolve_model(self.profile["model"])
        self.conversation_manager = ConversationManager()

    def _ensure_ollama_running(self):
        try:
            print("Checking Neural Link (Ollama)...")
            urllib.request.urlopen(OLLAMA_SETTINGS["base_url"], timeout=2)
            print("Neural Link: ONLINE")
        except Exception:
            print("TITAN Overlord: Waking local Ollama Brain in background...")
            try:
                if self.hud:
                    self.hud.update_status("Waking Brain...", "thinking")
            except Exception:
                pass
            # Force start ollama in the background
            try:
                subprocess.Popen(
                    "ollama serve", 
                    shell=True, 
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
                )
            except Exception:
                pass
            time.sleep(3)

    def _resolve_model(self, target_model):
        """Ensure the chosen model exists locally, fallback to known tags if not."""
        try:
            response = self.client.list()
            # Handle both old dict format and new object format from ollama library
            local_models = []
            if isinstance(response, dict):
                models_data = response.get('models', [])
                local_models = [m.get('name', '') if isinstance(m, dict) else str(m) for m in models_data]
            elif hasattr(response, 'models'):
                local_models = [m.model if hasattr(m, 'model') else str(m) for m in response.models]
            else:
                local_models = [str(m) for m in response] if response else []
            
            # Normalize model names (strip tag if comparing)
            def match_model(target, available):
                for m in available:
                    if target == m or target.split(':')[0] == m.split(':')[0]:
                        return m
                return None
            
            found = match_model(target_model, local_models)
            if found:
                print(f"JACK Brain: Model '{found}' confirmed available.")
                # Dashboard Sync
                try:
                    get_signals().emit_bridge("model_active", found, self.profile.get("description", "Active Profile"))
                except: pass
                return found
            
            # Smart Fallback Logic
            print(f"JACK Brain Warning: Model '{target_model}' not found in Ollama tags.")
            print(f"  Available models: {local_models}")
            
            # Multi-family fallback
            fallbacks = ["qwen2.5:7b", "llama3:latest", "llama3.2:latest", "mistral:latest", "gemma2:2b"]
            for fb in fallbacks:
                found = match_model(fb, local_models)
                if found:
                    print(f"JACK Brain: Falling back to available model - {found}")
                    return found
            
            # Last resort: first available model
            if local_models:
                print(f"JACK Brain: Using first available tag - {local_models[0]}")
                return local_models[0]
                
            return target_model # Return original and hope for the best if list failed
        except Exception as e:
            print(f"JACK Brain: Model resolution error ({e}), using default: {target_model}")
            return target_model

    def process_query(self, query):
        """Process a user query and return the appropriate response."""
        # --- TITAN REBIRTH BYPASS ---
        # Immediate neural handoff for self-maintenance commands
        task_low = query.lower()
        if any(
            word in task_low
            for word in [
                "reload jack",
                "restart jack",
                "reboot jack",
                "update jack",
                "jack reload",
            ]
        ):
            if self.hud:
                self.hud.update_status("Rebirthing Core...", "thinking")
            if self.hud:
                self.hud.set_tool_log("TITAN REBIRTH INITIATED")
            from skills.system_doctor.action import execute as restart_core

            restart_core("reload")
            return "At your command, Sir. Commencing Titan Rebirth. I will see you on the other side."

        if any(
            word in task_low
            for word in ["reinstall", "repair jack", "resync jack", "sync titan"]
        ):
            if self.hud:
                self.hud.update_status("Self-Healing...", "thinking")
            if self.hud:
                self.hud.set_tool_log("TITAN REPAIR INITIATED")
            import subprocess

            subprocess.Popen(
                ["python", "titan_installer.py"],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return "Initiating Immortal Self-Repair, Sir. I will reinstall my foundations and re-sync my sensors. Stand by."

        # New: Update command - remove old versions and update software
        if any(
            word in task_low
            for word in [
                "update",
                "upgrade",
                "update software",
                "upgrade software",
                "update system",
            ]
        ):
            if self.hud:
                self.hud.update_status("Updating System...", "thinking")
            if self.hud:
                self.hud.set_tool_log("TITAN UPDATE INITIATED")
            # Remove old version and reinstall
            import subprocess

            subprocess.Popen(
                ["python", "titan_installer.py", "--clean"],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            return "Updating your systems, Sir. I'll remove old versions and install the latest updates."

        if any(
            word in task_low
            for word in ["fix yourself", "debug yourself", "heal system", "fix jack"]
        ):
            if self.hud:
                self.hud.update_status("Architect Mode...", "thinking")
            from skills.auto_coder.action import execute as debug_core

            diagnosis = debug_core("diagnose")
            return f"Initiating Self-Diagnostic, Sir. {diagnosis}"

        if any(
            word in task_low
            for word in ["dashboard", "show nexus", "open nexus", "show reasoning"]
        ):
            if self.hud:
                self.hud.update_status("Launching Nexus...", "thinking")
            from nexus_bridge import get_signals

            if self.hud and hasattr(self.hud, "launch_nexus_dashboard"):
                self.hud.launch_nexus_dashboard()
            else:
                # Fallback launch if HUD reference is different
                import subprocess

                subprocess.Popen(
                    ["python", "dashboard.py"],
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            return "Materializing the Nexus Dashboard, Sir. Initializing neural visualizers."
        # ----------------------------

        try:
            print(f"Thinking (Ollama: {self.model})...")

            # Dashboard Sync Pulse
            try: get_signals().emit_bridge("neural_pulse", random.randint(5, 15))
            except: pass

            # Check if autonomous mode should be used
            if self.conversation_manager.should_use_autonomous_mode(query):
                return self._process_autonomous_query(query)
            else:
                return self._process_single_query(query)

        except Exception as e:
            import logging
            error_msg = str(e)
            try: get_signals().emit_bridge("pipeline_stage", "ERROR", f"AI Error: {error_msg[:60]}")
            except: pass
            if "Failed to connect to Ollama" in error_msg or "ConnectionRefusedError" in error_msg:
                user_msg = "I'm having trouble connecting to my local brain. Please ensure Ollama is running."
            else:
                user_msg = f"Sorry, I encountered an error: {error_msg}"
            
            logging.error(f"AI Processing Error: {error_msg}")
            print(f"Error in AI processing: {error_msg}")
            return user_msg

    async def process_query_async(self, query):
        """Asynchronous version of process_query for the autonomous loop."""
        task_low = query.lower()
        
        # Immediate neural handoffs (Same as sync version)
        if any(word in task_low for word in ["reload jack", "restart jack", "update jack"]):
            return self.process_query(query)

        try:
            print(f"Thinking (Ollama Async: {self.model})...")
            get_signals().emit_bridge("thought_received", f"Neural Synthesis: Engaging {self.model}...", "thought")
            # For the J.A.R.V.I.S. Pivot: All missions go through the thinking loop
            return await self._process_single_query_async(query)
        except Exception as e:
            import logging
            logging.error(f"AI Async Error: {e}")
            return f"Neural Error: {str(e)}"

    async def _process_single_query_async(self, query):
        """Process a single query asynchronously with tool detection."""
        # Get conversation context
        context_messages = self.conversation_manager.get_context_messages()

        # Build messages with context
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(context_messages)
        messages.append({"role": "user", "content": query})

        # Process with Ollama
        try:
            tools = [{"type": "function", "function": f} for f in FUNCTIONS]
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=tools,
                options=self.profile["options"],
            )
        except Exception as e:
            # Fallback to chat if tools aren't supported by the model
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options=self.profile["options"],
            )
            response = {"message": {"content": _get_message(response).get("content", ""), "tool_calls": None}}

        message = _get_message(response)
        final_response = ""
        tool_calls_data = []

        # Handle tool calls
        if "tool_calls" in message and message["tool_calls"]:
            for tool_call in message["tool_calls"]:
                fn_name = tool_call["function"]["name"]
                fn_args = tool_call["function"]["arguments"]

                # Execute tool
                try:
                    get_signals().emit_bridge("pipeline_stage", "EXECUTING", f"Tool: {fn_name}")
                    get_signals().emit_bridge("tool_executed", fn_name, json.dumps(fn_args)[:100], "Running...")
                    get_signals().emit_bridge("neural_pulse", 12)
                except: pass
                tool_result = self._execute_function_manual(fn_name, fn_args)
                try:
                    get_signals().emit_bridge("tool_executed", fn_name, json.dumps(fn_args)[:100], str(tool_result)[:150])
                except: pass
                
                tool_calls_data.append({
                    "function": fn_name,
                    "arguments": json.dumps(fn_args),
                    "result": tool_result,
                })

            final_response = "Action completed, Sir."
        else:
            # Check for JSON sniffer as fallback
            json_tool = self._detect_json_tool_call(message.get("content", ""))
            if json_tool:
                fn_name = json_tool["name"]
                fn_args = json_tool["parameters"]
                tool_result = self._execute_function_manual(fn_name, fn_args)
                tool_calls_data.append({
                    "function": fn_name,
                    "arguments": json.dumps(fn_args),
                    "result": tool_result,
                })
                final_response = "Action completed, Sir."
            else:
                final_response = message.get("content", "")

        # Clean response for J.A.R.V.I.S. persona
        final_response = self._sanitize_persona_output(final_response)

        # Add to history
        self.conversation_manager.add_interaction(query, final_response, tool_calls_data)
        return final_response

    def _sanitize_persona_output(self, text):
        """Enforce strict J.A.R.V.I.S. 'Actions over Words' output."""
        if not text: return "Action completed, Sir."
        # Remove thoughts
        text = re.sub(r"<(thought|reasoning)>.*?</\1>", "", text, flags=re.DOTALL).strip()
        # Remove raw JSON
        if "{" in text and "}" in text:
            text = "Action completed, Sir."
        return text

    def _process_single_query(self, query):
        """Process a single query with context using Ollama."""
        # Get conversation context
        context_messages = self.conversation_manager.get_context_messages()

        # Build messages with context
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(context_messages)
        messages.append({"role": "user", "content": query})

        # Try with tools first, fallback to no tools if not supported
        try:
            tools = [{"type": "function", "function": f} for f in FUNCTIONS]
            # Emit: AI is thinking
            try:
                get_signals().emit_bridge("pipeline_stage", "THINKING", f"Model {self.model} reasoning...")
                get_signals().emit_bridge("thinking_token", f"Engaging {self.model} with {len(tools)} tools...")
                get_signals().emit_bridge("neural_pulse", 10)
            except: pass
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=tools,
                options=self.profile["options"],
            )
        except Exception as e:
            if "does not support tools" in str(e):
                # Fallback to chat without tools
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    options=self.profile["options"],
                )
                # Simulate message structure
                msg = _get_message(response)
                response = {
                    "message": {
                        "content": msg.get("content", ""),
                        "tool_calls": None,
                    }
                }
            else:
                raise e

        message = _get_message(response)
        final_response = ""
        tool_calls_data = []

        # Handle tool calls
        if "tool_calls" in message and message["tool_calls"]:
            responses_from_tools = []
            for tool_call in message["tool_calls"]:
                fn_name = tool_call["function"]["name"]
                fn_args = tool_call["function"]["arguments"]

                # Execute tool
                try:
                    get_signals().emit_bridge("pipeline_stage", "EXECUTING", f"Tool: {fn_name}")
                    get_signals().emit_bridge("tool_executed", fn_name, json.dumps(fn_args)[:100], "Running...")
                    get_signals().emit_bridge("neural_pulse", 12)
                except: pass
                tool_result = self._execute_function_manual(fn_name, fn_args)
                try:
                    get_signals().emit_bridge("tool_executed", fn_name, json.dumps(fn_args)[:100], str(tool_result)[:150])
                    get_signals().emit_bridge("thought_received", f"Tool '{fn_name}' → {str(tool_result)[:80]}", "decision")
                except: pass

                # --- AUTO-DEVELOPER OVERDRIVE ---
                if (
                    "error" in str(tool_result).lower()
                    or "exception" in str(tool_result).lower()
                ):
                    print(
                        f"TITAN ARCHITECT: Detected Tool Failure in '{fn_name}'. Proactively self-repairing..."
                    )
                    from skills.auto_coder.action import execute as debug_core

                    diagnosis = debug_core("diagnose")
                    tool_result = f"CRITICAL: '{fn_name}' failed with result '{tool_result}'. Log Diagnosis: {diagnosis}"
                # -------------------------------

                tool_calls_data.append(
                    {
                        "function": fn_name,
                        "arguments": json.dumps(fn_args),
                        "result": tool_result,
                    }
                )
                responses_from_tools.append(tool_result)

            if any(
                name in ["open_application", "open_any_url", "take_screenshot"]
                for name in [tc["function"]["name"] for tc in message["tool_calls"]]
            ):
                final_response = "" # Stay silent for simple actions
            else:
                # For information-based tools (time, search), refine for natural speech
                final_response = self._refine_tool_response(
                    query, responses_from_tools[0]
                )
        else:
            # Fallback: Check if the content contains a JSON tool call (The "JSON Sniffer")
            json_tool = self._detect_json_tool_call(message.get("content", ""))
            if json_tool:
                fn_name = json_tool["name"]
                fn_args = json_tool["parameters"]
                tool_result = self._execute_function_manual(fn_name, fn_args)
                tool_calls_data.append(
                    {
                        "function": fn_name,
                        "arguments": json.dumps(fn_args),
                        "result": tool_result,
                    }
                )

                if fn_name in ["open_application", "open_any_url", "take_screenshot"]:
                    final_response = "" # Stay silent
                else:
                    final_response = self._refine_tool_response(query, tool_result)
            else:
                final_response = message.get("content", "")

        # --- NEURAL TELEMETRY: Extract Thought Blocks ---
        thoughts = re.findall(
            r"<(thought|reasoning)>(.*?)</\1>", final_response, re.DOTALL
        )

        for _, thought_text in thoughts:
            clean_thought = thought_text.strip()
            # Emit to Dashboard (safe — get_signals never returns None)
            try:
                signals = get_signals()
                signals.thought_received.emit(clean_thought, "thought")
            except Exception:
                pass
            print(f"Neural Telemetry (Thought): {clean_thought[:50]}...")
            # Pulse for each thought extracted
            try: get_signals().emit_bridge("neural_pulse", len(clean_thought) // 10 + 5)
            except: pass

        # Clean the final response for the user (Remove thoughts and raw JSON artifacts)
        final_response = re.sub(
            r"<(thought|reasoning)>.*?</\1>", "", final_response, flags=re.DOTALL
        ).strip()
        
        # JSON & Parameter Sanitizer: Strips technical leakage from verbal response
        if any(marker in final_response for marker in ["{", "}", ":", "[", "(", "parameters"]):
            # 1. Remove standard JSON blocks
            final_response = re.sub(r"\{.*\}", "", final_response, flags=re.DOTALL)
            
            # 2. Nuclear Parentheses/Bracket Strip (Removes IDs like [button:123] or (0xABC))
            # Removes everything between () or [] if it contains a colon, a number, or hex markers
            final_response = re.sub(r"\[[^\]]*[:\d][^\]]*\]", "", final_response)
            final_response = re.sub(r"\([^)]*[:\d][^)]*\)", "", final_response)
            
            # 3. Remove 'naked' parameter keys (e.g., "app_name:", "target:")
            final_response = re.sub(r"\w+:\s*.*", "", final_response)
            
            # 4. Final cleanup of technical keywords
            forbidden = ["parameters", "arguments", "function", "name", "button", "control", "automation"]
            for word in forbidden:
                 pattern = re.compile(rf"\b{word}\w*\b", re.IGNORECASE)
                 final_response = pattern.sub("", final_response)
            
            final_response = re.sub(r"\s+", " ", final_response).strip(",. ")
            if final_response:
                print(f"DEBUG: Nuclear Sanitization applied. Cleaned: {final_response}")

        if not final_response:
            final_response = "Action completed, Sir." # Lean fallback

        # Add to conversation history
        self.conversation_manager.add_interaction(
            query, final_response, tool_calls_data
        )

        return final_response

    def _process_autonomous_query(self, query):
        """Process a complex query with autonomous multi-tool execution and self-correction."""
        print("System Overdrive: Activating Autonomous Brain...")
        if self.hud:
            self.hud.update_status("Synthesizing Plan...", "thinking")

        # Step 1: Create a plan
        plan = self._create_execution_plan(query)
        print(f"Plan: {plan}")

        # Step 2: Execute the plan with recursion and self-correction
        results = []
        tool_calls = []
        context = f"Original Goal: {query}\nPlan: {plan}\n"

        start_time = time.time()
        timeout_seconds = 60  # Skyvern-style watchdog: 1 minute per mission

        try:
            for i in range(self.conversation_manager.max_tool_calls):
                # Watchdog Check
                if time.time() - start_time > timeout_seconds:
                    print(
                        "Watchdog: Neural Jam detected. Aborting mission to prevent system hang."
                    )
                    results.append(
                        "Error: Mission duration exceeded safety limits (Neural Jam)."
                    )
                    break
                if self.hud:
                    self.hud.update_status(f"Step {i + 1}: Reasoning...", "thinking")

                # Get next action based on current state
                state_prompt = f"{context}\nResults so far: {results}\nDetermine the next action. If the goal is met, respond with 'COMPLETE'."

                next_action = self._get_next_action_advanced(state_prompt)

                if next_action["action"] == "complete":
                    break

                if next_action.get("tool_call"):
                    tc = next_action["tool_call"]
                    fn_name = tc["function"]["name"]
                    fn_args = tc["function"]["arguments"]

                    if self.hud:
                        self.hud.update_status(f"Acting: {fn_name}", "executing")

                    # Execute and capture result
                    print(f"Executing: {fn_name}({fn_args})")
                    tool_result = self._execute_function_manual(fn_name, fn_args)

                    # --- Recurrent Self-Correction Logic ---
                    if (
                        "Error" in str(tool_result)
                        or "Failed" in str(tool_result)
                        or "not found" in str(tool_result).lower()
                    ):
                        print(
                            f"Self-Correction: {fn_name} failed. Attempting alternative logic..."
                        )
                        if self.hud:
                            self.hud.update_status(
                                f"Retrying Step {i + 1}...", "pulsing"
                            )

                        # Strategy: If DOM/ID click fails, try Visual Recognition
                        if "click" in fn_name and "target_description" in fn_args:
                            from tools import visual_click

                            print(
                                "Strategy Change: Switching to Vision-Guided Precision..."
                            )
                            tool_result = visual_click(fn_args["target_description"])

                    # Log result and context
                    results.append(f"Step {i + 1} ({fn_name}): {tool_result}")
                    tool_calls.append(
                        {
                            "function": fn_name,
                            "arguments": json.dumps(fn_args),
                            "result": tool_result,
                        }
                    )

                    # Update context for the next reasoning step
                    context += f"\n- Result of {fn_name}: {tool_result}"

                time.sleep(0.5)

            # Step 3: Final response
            final_response = self._generate_final_response(query, results, plan)

        except Exception as e:
            final_response = f"System Overdrive encountered an error: {str(e)}"

        self.conversation_manager.add_interaction(query, final_response, tool_calls)
        return final_response

    def _get_next_action_advanced(self, state_context):
        """Highly reasoning-focused action selector with JSON fallback."""
        tools = [{"type": "function", "function": f} for f in FUNCTIONS]

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are the JACK Systems Controller. Analyze the results and decide the next step. If done, say COMPLETE.",
                },
                {"role": "user", "content": state_context},
            ],
            tools=tools,
        )

        message = _get_message(response)
        if "tool_calls" in message and message["tool_calls"]:
            return {"action": "execute", "tool_call": message["tool_calls"][0]}

        # JSON Sniffer Fallback
        json_tool = self._detect_json_tool_call(message.get("content", ""))
        if json_tool:
            return {
                "action": "execute",
                "tool_call": {
                    "function": {
                        "name": json_tool["name"],
                        "arguments": json_tool["parameters"],
                    }
                },
            }

        return {"action": "complete", "content": message.get("content", "")}

    def _create_execution_plan(self, query):
        """Create an execution plan using Ollama."""
        prompt = f"Task: {query}\nTools: {', '.join([f['name'] for f in FUNCTIONS])}\nCreate a concise 1-2 step plan."

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a task planner. Respond with a short step-by-step plan.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return _get_message(response).get("content", "")

    def _detect_json_tool_call(self, content):
        """Detect and parse raw JSON tool calls, handling lazy JSON from local models."""
        if not content:
            return None

        # 1. Try to find anything between { and }
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            return None
        
        raw_json = match.group()
        
        # 2. Try standard json library first
        try:
            data = json.loads(raw_json)
            return self._normalize_tool_data(data)
        except:
            pass

        # 3. 'Lazy JSON' Recovery: Add quotes to unquoted keys/values
        try:
            # Simple regex to fix unquoted keys: {key: "value"} -> {"key": "value"}
            fixed_json = re.sub(r'(\w+):', r'"\1":', raw_json)
            # Fix single quotes
            fixed_json = fixed_json.replace("'", '"')
            data = json.loads(fixed_json)
            return self._normalize_tool_data(data)
        except:
            pass
            
        return None

    def _normalize_tool_data(self, data):
        """Standardize naming variations from different model families."""
        name = data.get("name") or data.get("function") or data.get("tool")
        params = (
            data.get("parameters")
            or data.get("arguments")
            or data.get("args")
            or data.get("input")
            or {}
        )
        if name:
            return {"name": name, "parameters": params}
        return None

    def _generate_final_response(self, query, results, plan):
        """Generate final response based on tool results."""
        prompt = (
            f"Original query: {query}\nTool results: {results}\nSummarize for the user."
        )

        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are JACK. Be concise and witty."},
                {"role": "user", "content": prompt},
            ],
        )
        return _get_message(response).get("content", "")

    def _execute_function_manual(self, name, args):
        """Helper to call functions from tools.py."""
        print(f"Executing local tool: {name}")
        if self.hud:
            self.hud.update_status(f"Executing {name}...", "executing")
        
        # Intense pulse for tool execution
        try: get_signals().emit_bridge("neural_pulse", 25)
        except: pass

        if name in FUNCTION_MAP:
            try:
                # Handle different argument formats (dict or string)
                if isinstance(args, str):
                    args = json.loads(args)

                # Execute with keyword arguments
                return FUNCTION_MAP[name](**args)
            except Exception as e:
                # Check if the error is about image input not supported
                if (
                    "does not support image input" in str(e)
                    or "image" in str(e).lower()
                ):
                    return "Visual Engine Error: The current AI model does not support image input. Please switch to a multimodal model like LLaVA."
                else:
                    return f"Error executing {name}: {str(e)}"
        return f"Unknown tool: {name}"

    def _refine_tool_response(self, original_query, tool_result):
        """Refine tool output into a natural response."""
        prompt = f"User asked: {original_query}\nTool data: {tool_result}\nProvide a witty, concise response."

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are JACK. Be brief (max 15 words) and helpful. NEVER repeat raw JSON, dictionary parameters, or anything in the 'SYSTEM_UI_TREE_MAP'. If the tool returns a list of buttons or elements, just say you've found the controls and ask for the specific action.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        return _get_message(response).get("content", "")

    def get_conversation_stats(self):
        """Get statistics about conversation and tool usage."""
        return self.conversation_manager.get_execution_stats()

    def clear_conversation_history(self):
        """Clear conversation history."""
        self.conversation_manager.clear_history()
        return "Conversation history cleared."
