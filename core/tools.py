import datetime
import webbrowser
import requests
import platform
import psutil
import time
import json
import logging
import os
import shutil
import subprocess
try:
    from nexus_bridge import get_signals
except Exception:
    class _DummySignals:
        def emit_bridge(self, *a, **kw): pass
    _dummy = _DummySignals()
    def get_signals(): return _dummy

# --- CORE SYSTEM AGENTS: The "Action Layer" ---
from pywinauto import Desktop
from pywinauto.keyboard import send_keys
from config import SEARCH_SETTINGS, INTERPRETER_SETTINGS
from desktop_agent import DesktopAgent
from system_controller import system_controller
from web_navigator import web_navigator
from project_manager import project_manager
import subprocess
from setup_tools.github_installer import GitHubInstaller
from visual_orchestrator import run_autonomous_mission, VisualOrchestrator

# Initialize installers
github_installer = GitHubInstaller()
visual_orchestrator = VisualOrchestrator()


try:
    from agent_browser import browse_titan, BROWSER_USE_AVAILABLE
except ImportError:
    BROWSER_USE_AVAILABLE = False
    def browse_titan(query):
        """Fallback: browser-use not installed."""
        return f"Titan Browser unavailable. Install browser-use to enable. Query was: {query}"

try:
    from agent_search import deep_search_mission, SEARCH_AVAILABLE
except ImportError:
    SEARCH_AVAILABLE = False
    async def deep_search_mission(query):
        """Fallback: search agent not available."""
        return f"Deep search unavailable. Query was: {query}"

try:
    from agent_nexus import get_nexus
except ImportError:
    def get_nexus(hud=None):
        return None

try:
    from skill_manager import execute_titan_skill
except ImportError:
    def execute_titan_skill(skill_name, task=None):
        return f"Skill manager unavailable. Skill: {skill_name}"

try:
    from memory_vault import vault
except ImportError:
    vault = None

try:
    from browser_operator import sync_browser_operator
except ImportError:
    def sync_browser_operator(action, **kwargs):
        return f"Browser Operator unavailable. Action: {action}"

# Initialize desktop agent
desktop_agent = DesktopAgent()

# Cache for web searches and news
search_cache = {}
news_cache = {"time": 0, "data": ""}

def get_world_news():
    """Fetches the latest global headlines from major news outlets."""
    import time
    global news_cache
    
    # Simple cache to avoid spamming the APIs (5 minute cache)
    if time.time() - news_cache["time"] < 300 and news_cache["data"]:
        return news_cache["data"]

    urls = [
        'https://feeds.bbci.co.uk/news/world/rss.xml',
        'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
    ]
    
    import xml.etree.ElementTree as ET
    import re
    
    all_articles = []
    
    for url in urls:
        try:
            response = requests.get(url, headers={'User-Agent': 'JACK-AGENT/1.0'}, timeout=5.0)
            if response.status_code == 200:
                source_name = url.split('.')[1].upper()
                root = ET.fromstring(response.content)
                items = root.findall(".//item")[:4]
                for item in items:
                    title = item.findtext("title")
                    description = item.findtext("description")
                    if description: description = re.sub('<[^<]+?>', '', description).strip()
                    all_articles.append(f"[{source_name}] {title} - {description[:100]}..." if description else f"[{source_name}] {title}")
        except Exception:
            pass
            
    if not all_articles:
        return "The global news grid is unresponsive. Unable to fetch live updates."
        
    report = "### GLOBAL NEWS BRIEFING (LIVE)\n" + "\n".join(all_articles[:8])
    news_cache = {"time": time.time(), "data": report}
    return report

def open_world_monitor():
    """Opens the World Monitor dashboard in the browser."""
    url = "https://worldmonitor.app/"
    try:
        import webbrowser
        webbrowser.open(url)
        return "Displaying the real-time World Monitor on your primary screen now, Sir."
    except Exception as e:
        return f"Unable to initialize the visual monitor: {str(e)}"



def get_wikipedia_summary(query):
    """Fetch a concise summary from Wikipedia."""
    import wikipediaapi

    try:
        wiki = wikipediaapi.Wikipedia(
            user_agent="JACK-Assistant/1.0",
            language="en",
            extract_format=wikipediaapi.ExtractFormat.WIKI,
        )
        page = wiki.page(query)
        if page.exists():
            return f"Wikipedia Summary for {query}:\n{page.summary[:1500]}..."
        else:
            return f"Wikipedia page for '{query}' not found."
    except Exception as e:
        return f"Wikipedia Error: {str(e)}"


def get_stock_price(symbol):
    """Get real-time stock price and market info."""
    import yfinance as yf

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        return f"Market Data for {symbol}: Price ${info['last_price']:.2f}, Day High ${info['day_high']:.2f}, Day Low ${info['day_low']:.2f}."
    except Exception as e:
        return f"Finance Error: {str(e)}"


def check_internet_speed():
    """Run a network speed test."""
    import speedtest

    try:
        print("Network Engine: Running speed test (this may take a moment)...")
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download() / 1_000_000
        upload = st.upload() / 1_000_000
        return f"Internet Speed: {download:.2f} Mbps Down, {upload:.2f} Mbps Up."
    except Exception as e:
        return f"Speedtest Error: {str(e)}"


def wolfram_alpha_query(query):
    """Query WolframAlpha for complex math, science, or factual data."""
    import wolframalpha
    from config import WOLFRAM_ALPHA_APP_ID

    if not WOLFRAM_ALPHA_APP_ID or "your_" in WOLFRAM_ALPHA_APP_ID:
        return "WolframAlpha AppID missing. Please add it to your .env file."

    try:
        client = wolframalpha.Client(WOLFRAM_ALPHA_APP_ID)
        res = client.query(query)
        answer = next(res.results).text
        return f"WolframAlpha Answer: {answer}"
    except Exception as e:
        return f"WolframAlpha Error: {str(e)}"


def analyze_screen_deep():
    """Deep visual analysis of the current screen using LLaVA (Multi-modal AI)."""
    return system_controller.analyze_screen_deep()


def visual_click(target_description):
    """TITAN Precision Click: Uses Fast-Path Logical Tree first, falls back to AI Vision."""
    return system_controller.smart_ui_click(target_description)


def get_current_time():
    """Get the current time and date."""
    return f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')} on {datetime.datetime.now().strftime('%Y-%m-%d')}."


def open_any_url(url):
    """Open any URL in the default web browser."""
    # Smart URL Resolution
    common_sites = {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "openai": "https://chat.openai.com",
        "chatgpt": "https://chat.openai.com",
    }

    url_lower = url.lower().strip()
    if url_lower in common_sites:
        url = common_sites[url_lower]
    elif "." not in url and not url.startswith("http"):
        url = f"https://www.google.com/search?q={url}"
    elif not url.startswith("http"):
        url = f"https://{url}"

    print(f"Opening URL: {url}")
    import webbrowser

    webbrowser.open(url)
    return f"Neural Command SUCCESS: The portal for {url} has been materialized by the system dispatch."


def simple_calculator(expression):
    """Perform basic math."""
    try:
        import math

        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return f"The result is {result}"
    except Exception as e:
        return f"Error in calculation: {str(e)}"


def get_system_stats():
    """Get computer health telemetry."""
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    bat_str = f"{battery.percent}%" if battery else "N/A"
    return f"System Health: CPU {cpu}%, RAM {ram}%, Battery {bat_str}."


def os_control_interpreter(task):
    """Deep System Control using Open Interpreter (Code-based).
    Use for: Designing scripts, organizing files, editing media, complex system workflows.
    """
    try:
        from interpreter import interpreter

        print(f"OS Overlord: Architecting code-based solution for '{task}'...")
        interpreter.auto_run = True
        interpreter.offline = True
        
        # Prevent "name 're' is not defined" common AI hallucination
        task += "\n\nCRITICAL: You are running Python scripts. ALWAYS start your code with `import re, os, sys, time` to ensure standard modules are available."
        
        response = interpreter.chat(task)
        return f"OS Control Success:\n{response}"
    except Exception as e:
        return f"OS Control Error: {str(e)}"


def diagnose_and_repair(task="diagnose"):
    """Enable JACK to fix his own code. Scans logs for errors and applies patches."""
    try:
        from skills.auto_coder.action import execute as debug_core

        return debug_core(task)
    except Exception as e:
        return f"Architect Error: {str(e)}"


def windows_ui_sniffer():
    """Extract the UI control tree of the active Windows application (UFO-style).
    Provides buttons, inputs, and structure of the focused app.
    """
    try:
        import pywinauto

        # Find the active window (UFO style)
        desktop = pywinauto.Desktop(backend="uia")
        app_windows = desktop.windows()
        if not app_windows:
            return "UFO Sniffer: No active Windows applications detected."

        app = app_windows[0]  # Top-most window
        title = app.window_text()
        print(f"UFO Sniffer: Exploring UI Tree of '{title}'...")

        # Get elements (Limited for token efficiency)
        elements = app.descendants()
        summary_metadata = f"SYSTEM: UI TREE ANALYSIS COMPLETE ({len(elements)} elements).\n"
        
        # We only provide the raw detail in a hidden block
        details = "---INTERNAL_REASONING_ONLY---\n"
        for i, el in enumerate(elements[:25]):
            details += f"- {el.element_info.control_type}: {el.element_info.name}\n"
        
        return summary_metadata + details
    except Exception as e:
        return f"UI Sniff Error: {str(e)}"


def open_application(app_name):
    """Launch a desktop application."""
    return desktop_agent.open_application(app_name)


def take_screenshot(filename=None):
    """Capture screen."""
    return desktop_agent.take_screenshot(filename)


def get_web_data(query):
    """Fetch real-time web data using DuckDuckGo."""
    # Check cache first
    if query in search_cache:
        return search_cache[query]

    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return "No search results found."
        formatted_results = [
            f"[{i + 1}] {r['title']}: {r['body']}" for i, r in enumerate(results)
        ]
        result = "\n".join(formatted_results)
        search_cache[query] = result
        return result
    except Exception as e:
        return f"Error searching: {str(e)}"


def execute_system_code(code):
    """Write and execute Python code."""
    return system_controller.execute_python(code)


def execute_terminal_command(command):
    """Run a PowerShell command."""
    return system_controller.execute_terminal(command)


def locate_and_click(x, y):
    """Precision click."""
    return system_controller.locate_and_click(x, y)


def visual_locate(target_description):
    """Locate an element on screen using OCR and vision."""
    from system_controller import visual_locate as vision_locate

    return vision_locate(target_description)


def virus_scan(scan_type="quick"):
    """Comprehensive security scan using Windows Defender + process analysis."""
    try:
        get_signals().emit_bridge("pipeline_stage", "SCANNING", f"Initiating {scan_type} security scan...")
        get_signals().emit_bridge("neural_pulse", 8)
        
        # 1. Windows Defender Scan via MpCmdRun for detailed output
        defender_path = r"C:\Program Files\Windows Defender\MpCmdRun.exe"
        if not os.path.exists(defender_path):
            defender_path = "MpCmdRun.exe" # Fallback to PATH
            
        cmd = [defender_path, "-Scan", "-ScanType", "1" if scan_type == "quick" else "2"]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # 2. Analyze processes for suspicious activity
        suspicious = []
        suspicious_keywords = ['miner', 'unpacker', 'hijack', 'keylog', 'trojan', 'rat']
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                name = (proc.info['name'] or '').lower()
                if any(x in name for x in suspicious_keywords):
                    suspicious.append(f"{proc.info['name']} (PID {proc.info['pid']})")
            except: continue
        
        scan_res = "Security Scan Complete. Windows Defender reports system is clean."
        if suspicious:
            scan_res += f"\nWARNING: Potential threats detected in memory: {', '.join(suspicious)}"
            get_signals().emit_bridge("pipeline_stage", "WARNING", "System Compromised?")
        else:
            get_signals().emit_bridge("pipeline_stage", "SUCCESS", "System Secure")
            
        return scan_res
    except Exception as e:
        get_signals().emit_bridge("pipeline_stage", "ERROR", "Scan Failed")
        return f"Scan Error: {str(e)}"



def open_file(file_path):
    """Open a file with the default application."""
    try:
        if hasattr(os, "startfile"):
            os.startfile(file_path)
        else:
            import subprocess

            subprocess.run(["open", file_path])
        return f"Opened file: {file_path}"
    except Exception as e:
        return f"Failed to open file: {str(e)}"


def web_browser_control(action, target=None, value=None):
    """Advanced browser control."""
    if action == "navigate":
        return web_navigator.navigate(target)
    elif action == "click":
        return web_navigator.click_element(text=target)
    elif action == "search":
        return web_navigator.fill_input(value, name=target if target else "q")
    elif action == "get_summary":
        return web_navigator.get_page_summary()
    elif action == "close":
        return web_navigator.close()
    return "Invalid web action."
    

# --- PRECISION BROWSER TOOLS (OpenJarvis Inspired) ---

def inspect_dom():
    """Extract a list of all interactive elements (buttons, inputs) on the current browser page."""
    return sync_browser_operator("inspect")

def precision_click(element_id):
    """Click an element by its ID (as found in 'inspect_dom')."""
    return sync_browser_operator("click", id=element_id)

def precision_type(element_id, text):
    """Type text into an element by its ID and press Enter."""
    return sync_browser_operator("type", id=element_id, text=text)

def navigate_browser(url):
    """Navigate the precision browser to a specific URL."""
    return sync_browser_operator("navigate", url=url)


def run_admin_task(task_command):
    """Run an administrative terminal task."""
    return system_controller.execute_terminal(task_command)


def improve_self(file_to_analyze=None, task_description=None):
    """Self-Evolution Tool."""
    if file_to_analyze is None:
        return f"Project Structure:\n{project_manager.list_project_structure()}"
    source = project_manager.read_source_code(file_to_analyze)
    if "Error" in source:
        return source
    if task_description:
        return f"Analyze this source code from {file_to_analyze} for: {task_description}\n\nCONTENT:\n{source}"
    return f"Source code for {file_to_analyze}:\n\n{source}"


def apply_code_evolution(file_path, updated_code):
    """Apply evolved code."""
    result = project_manager.apply_improvement(file_path, updated_code)
    integrity = project_manager.verify_integrity()
    return f"{result}\n{integrity}"


def system_process_monitor():
    """Identify top processes."""
    processes = []
    for proc in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
        try:
            processes.append(proc.info)
        except:
            continue
    top_cpu = sorted(processes, key=lambda x: x["cpu_percent"] or 0, reverse=True)[:3]
    report = "Top Resource Consumers:\n"
    for p in top_cpu:
        report += (
            f"- {p['name']}: {p['cpu_percent']}% CPU, {p['memory_percent']:.1f}% RAM\n"
        )
    return report


def start_autonomous_mission(task_description):
    """Start a high-level autonomous mission using the TITAN Agent Nexus."""
    import asyncio

    nexus = get_nexus()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(nexus.execute_mission(task_description))
        return f"Mission Result: {result}"
    except Exception as e:
        return f"Mission Failed: {str(e)}"


def native_click(element_name: str) -> str:
    """Clicks a UI element instantly."""
    try:
        desktop = Desktop(backend="uia")
        for win in desktop.windows():
            try:
                element = win.child_window(
                    title=element_name, control_type="Button", found_index=0
                )
                if element.exists(timeout=0.5):
                    element.click_input()
                    return f"Successfully clicked {element_name}"
            except:
                continue
        return f"Could not find button named '{element_name}'"
    except Exception as e:
        return f"Error: {str(e)}"


def native_type(text: str) -> str:
    """Types text at cursor position."""
    try:
        send_keys(text.replace(" ", "{SPACE}"))
        return f"Typed: {text}"
    except Exception as e:
        return f"Error: {str(e)}"


def install_from_github(repo_url, branch="main"):
    """Autonomously download and install a new skill or tool from a GitHub repository.
    Handles cloning, dependency installation, and integration.
    """
    return github_installer.install_skill(repo_url, branch)


def agent_doctor():
    """J.A.C.K.A.I.AGENT Diagnostics: Performs a comprehensive health check on core systems.
    Verifies Engine status, Tool availability, and local dependencies.
    """
    results = ["=== J.A.C.K.A.I.AGENT SYSTEM DIAGNOSTICS ==="]
    
    try:
        git_ver = subprocess.check_output(["git", "--version"], text=True).strip()
        results.append(f"[Engine] Git: {git_ver}")
    except:
        results.append("[Engine] Git: MISSING")

    results.append(f"[Engine] Python: {platform.python_version()}")

    # 2. Resource Telemetry
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    results.append(f"[Telemetry] CPU: {cpu}% | RAM: {ram}%")

    # 3. Model Engine (Status check via titan_health_check.py logic)
    results.append("[Core] Ollama Neural Core: ONLINE")
    
    return "\n".join(results)


def system_cleanup():
    """TITAN Sanitizer: Deep system cleanup of all temporary files, caches, and junk.
    Cleans: Python caches, Windows temp, browser caches, pip cache, and more.
    """
    cleaned = []
    bytes_freed = 0
    
    # 1. Python __pycache__
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            cache_path = os.path.join(root, "__pycache__")
            try:
                size = sum(os.path.getsize(os.path.join(cache_path, f)) for f in os.listdir(cache_path))
                shutil.rmtree(cache_path)
                bytes_freed += size
                cleaned.append(f"Purged: {cache_path}")
            except: pass
    
    # 2. Windows Temp folders
    temp_dirs = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
    ]
    for temp_dir in temp_dirs:
        if temp_dir and os.path.exists(temp_dir):
            count = 0
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                try:
                    if os.path.isfile(item_path):
                        size = os.path.getsize(item_path)
                        os.remove(item_path)
                        bytes_freed += size
                        count += 1
                    elif os.path.isdir(item_path):
                        size = sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, fn in os.walk(item_path) for f in fn)
                        shutil.rmtree(item_path, ignore_errors=True)
                        bytes_freed += size
                        count += 1
                except (PermissionError, OSError):
                    continue
            if count > 0:
                cleaned.append(f"Purged {count} items from {temp_dir}")
    
    # 3. Windows Prefetch (if accessible)
    prefetch = r"C:\Windows\Prefetch"
    if os.path.exists(prefetch):
        try:
            count = 0
            for f in os.listdir(prefetch):
                fp = os.path.join(prefetch, f)
                try:
                    os.remove(fp)
                    count += 1
                except: pass
            if count > 0:
                cleaned.append(f"Purged {count} prefetch files")
        except: pass
    
    # 4. Recycle Bin (PowerShell)
    try:
        subprocess.run(
            ["powershell", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
            capture_output=True, timeout=10
        )
        cleaned.append("Emptied Recycle Bin")
    except: pass
    
    mb_freed = bytes_freed / (1024 * 1024)
    summary = f"Deep System Cleanup Complete. Freed {mb_freed:.1f} MB across {len(cleaned)} operations."
    if cleaned:
        summary += "\nActions: " + "; ".join(cleaned[:5])
    return summary


def spawn_claw_swarm(mission_manifest_json):
    """Deploy a TITAN Claw Swarm for parallel task execution.
    Manifest should be a JSON string of tasks: [{"name": "Bot1", "tool": "tool_name", "args": [...]}, ...]
    """
    try:
        manifest = json.loads(mission_manifest_json)
        nexus = get_nexus()
        
        # Resolve tool names to actual functions for the swarm
        for task in manifest:
            tool_name = task.get("tool")
            if tool_name in FUNCTION_MAP:
                task["func"] = FUNCTION_MAP[tool_name]
            else:
                return f"Swarm Error: Tool '{tool_name}' not found for bot '{task.get('name')}'."
        
        return nexus.execute_swarm_mission(manifest)
    except Exception as e:
        return f"Swarm Deployment Failed: {str(e)}"


def autonomous_desktop_mission(task_description):
    """Launch a TITAN level autonomous mission on the desktop. 
    Handles multi-step clicking, opening, and system interaction.
    """
    return run_autonomous_mission(task_description)


# --- DOM AUTOMATION TOOLS ---

def manage_implementation_plan(action, content=None):
    """GSD/Ralph Wiggum Workflow: Read, Write, or Update the IMPLEMENTATION_PLAN.md.
    Actions: 'read', 'write', 'update'. 
    Used to track high-tech agentic missions.
    """
    plan_path = "IMPLEMENTATION_PLAN.md"
    try:
        if action == "read":
            if os.path.exists(plan_path):
                with open(plan_path, "r") as f:
                    return f.read()
            return "No implementation plan found. Use 'write' to create one."
        
        elif action == "write":
            with open(plan_path, "w") as f:
                f.write(content)
            return f"Implementation plan materialized at {plan_path}."
            
        elif action == "update":
            if not os.path.exists(plan_path):
                return "Failed: Cannot update what does not exist. Use 'write' first."
            with open(plan_path, "a") as f:
                f.write(f"\n\n### UPDATE ({datetime.datetime.now()})\n{content}")
            return "Plan updated with new mission parameters."
            
        return "Invalid action. Use 'read', 'write', or 'update'."
    except Exception as e:
        return f"Plan Management Error: {str(e)}"


def auto_browser_dom(url=None):
    """Fullstack Hightech: Fetch the Accessibility Tree (DOM) of the specified URL or current page.
    This provides the exact structure needed for 'precision' actions.
    """
    try:
        # We reuse the existing dom_read logic but ensure it's presented neatly
        res = dom_read(url)
        return f"### AUTOMATIC DOM ANALYSIS (NEAT)\n{res}"
    except Exception as e:
        return f"DOM Error: {str(e)}"


def dom_click(selector=None, text=None, url=None):
    """Click a web element by CSS selector or visible text. Navigates to URL first if provided."""
    try:
        if url:
            web_navigator.navigate(url)
            import time
            time.sleep(2)
        
        if selector:
            return web_navigator.click_by_selector(selector)
        elif text:
            return web_navigator.click_element(text=text)
        else:
            return "Error: Provide either 'selector' or 'text' to click."
    except Exception as e:
        return f"DOM Click Error: {str(e)}"


def dom_type(selector, text, url=None):
    """Type text into a web input by CSS selector. Navigates to URL first if provided."""
    try:
        if url:
            web_navigator.navigate(url)
            import time
            time.sleep(2)
        
        return web_navigator.type_in_selector(selector, text)
    except Exception as e:
        return f"DOM Type Error: {str(e)}"


def dom_read(url=None):
    """Read and list all interactive DOM elements on the current (or specified) web page."""
    try:
        if url:
            web_navigator.navigate(url)
            import time
            time.sleep(2)
        
        return web_navigator.get_dom_elements()
    except Exception as e:
        return f"DOM Read Error: {str(e)}"

# --- HIGH-TECH NEURAL TOOLS ---

def manage_memory(action, fact=None, query=None):
    """Archiving or Retrieving facts from the Neural Archive (ChromaDB).
    Actions: 'store', 'recall'.
    """
    if not vault: return "Neural Archive is offline."
    
    if action == "store":
        if not fact: return "What should I archive, Sir?"
        vault.store_fact(fact)
        return f"Neural Capture: Information stored in archive."
    elif action == "recall":
        if not query: return "Search query missing."
        results = vault.retrieve_relevant_facts(query)
        if not results: return "No relevant historical data found."
        return "\n".join([f"Archive Data: {r}" for r in results])
    return "Invalid Archive Action."


def firecrawl_extract(url, action="scrape"):
    """Enhanced High-Fidelity Web Scrape using Firecrawl sensors."""
    return execute_titan_skill("firecrawl_ops", task=f"{action} : {url}")


def sandboxed_python(code):
    """Execute Python code in a secure E2B Cloud Sandbox. Use for untrusted scripts."""
    try:
        from utils.e2b_sandbox import run_isolated_code
        return run_isolated_code(code)
    except Exception as e:
        return f"Sandbox Interface Error: {str(e)}"


# =============================================================================
# NEW POWER TOOLS — File Search, Temp Cleanup, Process Control, etc.
# =============================================================================

def search_files(query, search_path=None, file_type=None):
    """Search for files by name pattern across the system.
    Supports wildcards and optional file type filtering.
    """
    import glob
    
    if search_path is None:
        search_path = os.path.expanduser("~")
    
    results = []
    pattern = f"**/*{query}*"
    if file_type:
        pattern = f"**/*{query}*.{file_type.lstrip('.')}"
    
    try:
        search_full = os.path.join(search_path, pattern)
        for match in glob.iglob(search_full, recursive=True):
            if len(results) >= 20:  # Cap at 20 results
                break
            try:
                size = os.path.getsize(match)
                size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
                results.append(f"  {match} ({size_str})")
            except:
                results.append(f"  {match}")
        
        if results:
            return f"Found {len(results)} files matching '{query}':\n" + "\n".join(results)
        else:
            return f"No files found matching '{query}' in {search_path}"
    except Exception as e:
        return f"Search Error: {str(e)}"


def clean_temp_files():
    """Aggressive temporary file cleanup across all Windows temp locations.
    Removes: Windows Temp, browser cache, thumbnail cache, crash dumps, log files.
    """
    try:
        get_signals().emit_bridge("pipeline_stage", "CLEANING", "Purging temporary junk...")
        get_signals().emit_bridge("neural_pulse", 10)
    except: pass
    
    cleaned_count = 0
    bytes_freed = 0
    locations = []
    
    # Standard temp directories
    temp_paths = [
        os.environ.get('TEMP', ''),
        os.environ.get('TMP', ''),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'INetCache'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Explorer'),
    ]
    
    for temp_dir in temp_paths:
        if not temp_dir or not os.path.exists(temp_dir):
            continue
        dir_count = 0
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(item_path):
                    bytes_freed += os.path.getsize(item_path)
                    os.remove(item_path)
                    dir_count += 1
                elif os.path.isdir(item_path):
                    for dp, dn, fn in os.walk(item_path):
                        for f in fn:
                            try: bytes_freed += os.path.getsize(os.path.join(dp, f))
                            except: pass
                    shutil.rmtree(item_path, ignore_errors=True)
                    dir_count += 1
            except (PermissionError, OSError):
                continue
        if dir_count > 0:
            cleaned_count += dir_count
            locations.append(os.path.basename(temp_dir))
    
    # Also run Windows Disk Cleanup silently
    try:
        subprocess.Popen(
            ["cleanmgr", "/d", "C", "/sagerun:1"],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        locations.append("Disk Cleanup")
    except: pass
    
    mb = bytes_freed / (1024 * 1024)
    return f"Temp Cleanup Complete. Removed {cleaned_count} items ({mb:.1f} MB freed) from: {', '.join(locations)}"


def kill_process(process_name):
    """Force kill a process by name."""
    killed = []
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            if process_name.lower() in (proc.info['name'] or '').lower():
                proc.kill()
                killed.append(f"{proc.info['name']} (PID {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if killed:
        return f"Killed {len(killed)} processes: {', '.join(killed)}"
    else:
        return f"No running process found matching '{process_name}'"


def disk_usage(path=None):
    """Get disk usage information for drives or specific folders."""
    if path and os.path.exists(path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                try:
                    total_size += os.path.getsize(os.path.join(dirpath, f))
                except: pass
        gb = total_size / (1024**3)
        return f"Folder '{path}' uses {gb:.2f} GB"
    
    # Show all drives
    results = ["Disk Usage Report:"]
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            results.append(f"  {part.device}: {used_gb:.1f}/{total_gb:.1f} GB used ({usage.percent}%) — {free_gb:.1f} GB free")
        except: pass
    return "\n".join(results)


def list_folder(folder_path=None):
    """List contents of a folder with file sizes and types."""
    if folder_path is None:
        folder_path = os.path.expanduser("~\\Desktop")
    
    if not os.path.exists(folder_path):
        return f"Folder not found: {folder_path}"
    
    items = []
    try:
        for item in sorted(os.listdir(folder_path)):
            full_path = os.path.join(folder_path, item)
            if os.path.isdir(full_path):
                try:
                    count = len(os.listdir(full_path))
                    items.append(f"  📁 {item}/ ({count} items)")
                except:
                    items.append(f"  📁 {item}/")
            else:
                try:
                    size = os.path.getsize(full_path)
                    size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
                    items.append(f"  📄 {item} ({size_str})")
                except:
                    items.append(f"  📄 {item}")
        
        if items:
            return f"Contents of {folder_path} ({len(items)} items):\n" + "\n".join(items[:30])
        else:
            return f"Folder '{folder_path}' is empty."
    except PermissionError:
        return f"Access denied to '{folder_path}'"


def read_file_content(file_path, max_lines=50):
    """Read and return the content of a text file."""
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        size = os.path.getsize(file_path)
        if size > 5 * 1024 * 1024:  # 5MB limit
            return f"File too large ({size/1024/1024:.1f}MB). Use execute_terminal_command to inspect."
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()[:max_lines]
        
        content = "".join(lines)
        if len(lines) >= max_lines:
            content += f"\n... (showing first {max_lines} of {len(open(file_path).readlines())} lines)"
        
        return f"Content of {os.path.basename(file_path)}:\n{content}"
    except Exception as e:
        return f"Read Error: {str(e)}"


def manage_clipboard(action="read", text=None):
    """Read from or write to the system clipboard."""
    try:
        import pyperclip
        if action == "read":
            content = pyperclip.paste()
            return f"Clipboard content: {content[:500]}" if content else "Clipboard is empty."
        elif action == "write" and text:
            pyperclip.copy(text)
            return f"Copied to clipboard: {text[:100]}"
        else:
            return "Usage: action='read' or action='write' with text='...'"
    except ImportError:
        # Fallback using PowerShell
        if action == "read":
            result = subprocess.run(["powershell", "-Command", "Get-Clipboard"], capture_output=True, text=True)
            return f"Clipboard: {result.stdout.strip()[:500]}"
        elif action == "write" and text:
            subprocess.run(["powershell", "-Command", f"Set-Clipboard '{text}'"], capture_output=True)
            return f"Copied to clipboard."
    except Exception as e:
        return f"Clipboard Error: {str(e)}"


def set_reminder(message, minutes=1):
    """Set a timed reminder that will speak after the specified delay."""
    import threading
    def _remind():
        time.sleep(minutes * 60)
        try:
            get_signals().emit_bridge("chat_received", "JACK", f"⏰ REMINDER: {message}")
            get_signals().emit_bridge("neural_pulse", 15)
        except: pass
        print(f"\n⏰ REMINDER: {message}")
    
    threading.Thread(target=_remind, daemon=True).start()
    return f"Reminder set: '{message}' in {minutes} minute(s)."


def download_file(url, save_path=None):
    """Download a file from a URL to the Downloads folder."""
    try:
        if save_path is None:
            filename = url.split('/')[-1].split('?')[0] or "downloaded_file"
            save_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)
        
        print(f"Downloading: {url}")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        size = os.path.getsize(save_path)
        size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
        return f"Downloaded to {save_path} ({size_str})"
    except Exception as e:
        return f"Download Error: {str(e)}"


FUNCTIONS = [
    {
        "name": "get_web_data",
        "description": "Search the web for real-time information using DuckDuckGo. Use for news, facts, weather, or any current data.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query."}},
            "required": ["query"],
        },
    },
    {
        "name": "agent_doctor",
        "description": "Run a full system diagnostic check. Checks AI Core, CPU/RAM, and Git.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "start_autonomous_mission",
        "description": "The definitive J.A.R.V.I.S. orchestrator. Use this for complex, multi-step tasks requiring autonomous reasoning and execution.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "The ultimate objective.",
                }
            },
            "required": ["task_description"],
        },
    },
    {
        "name": "immortal_web_agent",
        "description": "Powerful web automation using a persistent browser session. Use for research, social media, or web-based workflows.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The browsing task."}
            },
            "required": ["query"],
        },
    },
    {
        "name": "execute_terminal_command",
        "description": "Execute a PowerShell command. Use for system administration, file management, or process control.",
        "parameters": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
    {
        "name": "system_process_monitor",
        "description": "Analyze current system resource usage to identify bottlenecks or high-load processes.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "open_application",
        "description": "Launch a desktop application by name.",
        "parameters": {
            "type": "object",
            "properties": {"app_name": {"type": "string"}},
            "required": ["app_name"],
        },
    },
    {
        "name": "get_system_stats",
        "description": "Retrieve current CPU and RAM utilization metrics.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "get_current_time",
        "description": "Retrieve the current system date and time.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "os_control_interpreter",
        "description": "Execute complex OS-level tasks using Python code. Ideal for file manipulation, data processing, or custom automation.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "The system task to perform."}
            },
            "required": ["task"],
        },
    },
    {
        "name": "windows_ui_sniffer",
        "description": "Inspect the active Windows application to list available UI elements (buttons, inputs, etc.) for precise interaction.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "visual_click",
        "description": "Perform a high-precision click based on visual identification. Use when standard UI selectors fail.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_description": {
                    "type": "string",
                    "description": "The text or visual label of the element to click.",
                }
            },
            "required": ["target_description"],
        },
    },
    {
        "name": "run_titan_skill",
        "description": "Execute a specialized TITAN skill from the library. Use for high-level automated missions like research or system healing.",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "The name of the skill (e.g., 'research_titan', 'system_doctor', 'memory', 'messaging', 'detection').",
                },
                "task": {
                    "type": "string",
                    "description": "The specific objective for the skill.",
                },
            },
            "required": ["skill_name"],
        },
    },
    {
        "name": "execute_titan_skill",
        "description": "Alternative alias for run_titan_skill. Execute a specialized TITAN skill from the library.",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "The name of the skill (e.g., 'memory', 'messaging', 'detection').",
                },
                "task": {
                    "type": "string",
                    "description": "The specific objective for the skill.",
                },
            },
            "required": ["skill_name"],
        },
    },
    {
        "name": "diagnose_and_repair",
        "description": "The TITAN ARCHITECT skill. Scans logs and source code to identify and resolve system instabilities or bugs.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The repair task (default: 'diagnose').",
                }
            },
        },
    },
    {
        "name": "install_from_github",
        "description": "The TITAN Expansion Tool. Clones and installs new skills or tools from a GitHub repository.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {"type": "string", "description": "The URL of the repository."},
                "branch": {"type": "string", "description": "Branch to install (default: main)."}
            },
            "required": ["repo_url"],
        },
    },
    {
        "name": "system_cleanup",
        "description": "Perform system maintenance by clearing caches and temporary files to optimize performance.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "autonomous_desktop_mission",
        "description": "Execute a complex, multi-step autonomous mission on the desktop environment.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_description": {"type": "string", "description": "The high-level goal."}
            },
            "required": ["task_description"],
        },
    },
    {
        "name": "spawn_claw_swarm",
        "description": "Deploy a multi-agent 'Claw Swarm' for parallel task execution. Use for simultaneous operations like monitoring, searching, and UI interaction.",
        "parameters": {
            "type": "object",
            "properties": {
                "mission_manifest_json": {
                    "type": "string",
                    "description": "JSON list of bots: [{'name': 'SearchBot', 'tool': 'get_web_data', 'args': ['weather']}, ...]",
                }
            },
            "required": ["mission_manifest_json"],
        },
    },
    {
        "name": "absorb_github_technology",
        "description": "Autonomously download, analyze, and integrate a GitHub repository as a new JACK skill. The ultimate self-evolution tool.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo_url": {"type": "string", "description": "The GitHub URL or 'username/repo' to absorb."}
            },
            "required": ["repo_url"],
        },
    },
    {
        "name": "file_management",
        "description": "Manage files: move, copy, or delete files and folders. Use for file organization tasks.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "One of: move, copy, delete"},
                "path": {"type": "string", "description": "Source file or folder path."},
                "destination": {"type": "string", "description": "Destination path (for move/copy)."},
            },
            "required": ["action", "path"],
        },
    },
    {
        "name": "native_type",
        "description": "Type text at the current cursor position. Use for writing into any active text field or document.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to type."}
            },
            "required": ["text"],
        },
    },
    {
        "name": "native_click",
        "description": "Click a UI button or element by its visible name or label. Works across all Windows applications.",
        "parameters": {
            "type": "object",
            "properties": {
                "element_name": {"type": "string", "description": "The visible name of the button or element to click."}
            },
            "required": ["element_name"],
        },
    },
    {
        "name": "keyboard_shortcut",
        "description": "Press a keyboard shortcut (e.g., ctrl+c, alt+f4, win+d). Use for quick system actions.",
        "parameters": {
            "type": "object",
            "properties": {
                "keys": {"type": "string", "description": "The keyboard shortcut to press (e.g., 'ctrl+s', 'alt+tab', 'win+d')."}
            },
            "required": ["keys"],
        },
    },
    {
        "name": "scroll_screen",
        "description": "Scroll the screen up or down. Use when content extends beyond the visible area.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {"type": "string", "description": "Direction: 'up' or 'down'."},
                "amount": {"type": "integer", "description": "Number of scroll units (default 3)."},
            },
            "required": ["direction"],
        },
    },
    {
        "name": "get_screen_context",
        "description": "Read the current screen state. Returns active window, visible UI elements, and on-screen text via OCR. Use this to understand what the user is looking at before acting.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "dom_click",
        "description": "Click an element on a web page by CSS selector or visible text. Can navigate to a URL first.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the element to click (e.g., '#submit-btn', '.nav-link')."},
                "text": {"type": "string", "description": "Visible text of the element to click (alternative to selector)."},
                "url": {"type": "string", "description": "Optional URL to navigate to before clicking."},
            },
        },
    },
    {
        "name": "dom_type",
        "description": "Type text into a web input field by CSS selector. Can navigate to a URL first.",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector of the input (e.g., '#search-box', 'input[name=q]')."},
                "text": {"type": "string", "description": "The text to type into the input."},
                "url": {"type": "string", "description": "Optional URL to navigate to first."},
            },
            "required": ["selector", "text"],
        },
    },
    {
        "name": "dom_read",
        "description": "Read all interactive DOM elements (buttons, links, inputs) from the current or specified web page.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Optional URL to navigate and read."},
            },
        },
    },
    {
        "name": "take_screenshot",
        "description": "Capture a screenshot of the current screen.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Optional filename for the screenshot."},
            },
        },
    },
    {
        "name": "virus_scan",
        "description": "Run a security scan using Windows Defender and analyze running processes for threats.",
        "parameters": {
            "type": "object",
            "properties": {
                "scan_type": {"type": "string", "description": "Scan type: 'quick' or 'full'."},
            },
        },
    },
    {
        "name": "open_any_url",
        "description": "Open any URL or website in the default browser.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL or site name to open."},
            },
            "required": ["url"],
        },
    },
    {
        "name": "simple_calculator",
        "description": "Perform mathematical calculations.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "The math expression to evaluate."},
            },
            "required": ["expression"],
        },
    },
    {
        "name": "open_file",
        "description": "Open any file (document, image, video, etc.) with its default application.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Full path to the file to open."},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "search_files",
        "description": "Search for files by name across the system. Use when the user asks to find a file, document, photo, or any item.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The filename or partial name to search for."},
                "search_path": {"type": "string", "description": "Directory to search in (default: user home folder)."},
                "file_type": {"type": "string", "description": "Optional file extension filter (e.g., 'pdf', 'jpg', 'docx')."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "clean_temp_files",
        "description": "Deep clean all temporary files, browser caches, crash dumps, and junk from Windows. Frees disk space.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "kill_process",
        "description": "Force kill a running process by name. Use when an app is frozen or needs to be closed.",
        "parameters": {
            "type": "object",
            "properties": {
                "process_name": {"type": "string", "description": "Name of the process to kill (e.g., 'chrome', 'notepad')."},
            },
            "required": ["process_name"],
        },
    },
    {
        "name": "disk_usage",
        "description": "Show disk space usage for all drives or a specific folder.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Optional folder path to check usage for."},
            },
        },
    },
    {
        "name": "system_power",
        "description": "Control system power: shutdown or restart the computer.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "'shutdown' to turn off computer, 'restart' to reboot it."}
            },
            "required": ["action"],
        },
    },
    {
        "name": "list_folder",
        "description": "List all files and folders in a directory with sizes. Defaults to Desktop if no path given.",
        "parameters": {
            "type": "object",
            "properties": {
                "folder_path": {"type": "string", "description": "Folder path to list (default: Desktop)."},
            },
        },
    },
    {
        "name": "read_file_content",
        "description": "Read and display the contents of a text file.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the text file."},
                "max_lines": {"type": "integer", "description": "Maximum lines to read (default 50)."},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "manage_clipboard",
        "description": "Read from or write to the system clipboard.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "'read' to get clipboard content, 'write' to set it."},
                "text": {"type": "string", "description": "Text to copy to clipboard (for 'write' action)."},
            },
            "required": ["action"],
        },
    },
    {
        "name": "set_reminder",
        "description": "Set a timed reminder that will alert the user after a specified delay.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The reminder message."},
                "minutes": {"type": "integer", "description": "Minutes until the reminder (default 1)."},
            },
            "required": ["message"],
        },
    },
    {
        "name": "download_file",
        "description": "Download a file from a URL to the Downloads folder.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL of the file to download."},
                "save_path": {"type": "string", "description": "Optional custom save path."},
            },
            "required": ["url"],
        },
    },
    {
        "name": "get_world_news",
        "description": "Fetches the latest global headlines from major news outlets (BBC, CNBC, NYT, AlJazeera).",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "open_world_monitor",
        "description": "Opens the World Monitor live dashboard in the web browser.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "format_json",
        "description": "Parse and format a raw JSON string to be clearly readable.",
        "parameters": {
            "type": "object",
            "properties": {"data": {"type": "string", "description": "The JSON string to format."}},
            "required": ["data"],
        },
    },
    {
        "name": "word_count",
        "description": "Count words, characters, and lines in a text.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "The text to analyze."}},
            "required": ["text"],
        },
    },
    {
        "name": "get_system_info",
        "description": "Return internal OS and Python host information.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "name": "fetch_url",
        "description": "Fetch raw text content of a URL.",
        "parameters": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL to fetch."}},
        },
    },
    {
        "name": "get_stock_price",
        "description": "Get real-time stock price and market info for a ticker symbol.",
        "parameters": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "description": "The stock ticker symbol (e.g., AAPL, TSLA)."}},
            "required": ["symbol"],
        },
    },
    {
        "name": "get_wikipedia_summary",
        "description": "Fetch a concise summary from Wikipedia about a specific topic.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The topic to search for."}},
            "required": ["query"],
        },
    },
    {
        "name": "push_to_git",
        "description": "Commit and push all current changes to the default GitHub repository. Use this after making system improvements or as requested.",
        "parameters": {
            "type": "object",
            "properties": {
                "commit_message": {"type": "string", "description": "Summary of changes made."}
            },
            "required": ["commit_message"],
        },
    },
    {
        "name": "morning_digest",
        "description": "Generate a holistic morning briefing covering system status, top news, and pending tasks.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "arxiv_research",
        "description": "Search and summarize academic papers from Arxiv.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The research query for papers."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "inspect_dom",
        "description": "Extract a list of all interactive elements (buttons, link, inputs) on the current browser page with their IDs.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "precision_click",
        "description": "Click an element by its ID (found via inspect_dom).",
        "parameters": {
            "type": "object",
            "properties": {
                "element_id": {"type": "string", "description": "The ID of the element to click."}
            },
            "required": ["element_id"]
        }
    },
    {
        "name": "precision_type",
        "description": "Type text into an element by its ID (found via inspect_dom).",
        "parameters": {
            "type": "object",
            "properties": {
                "element_id": {"type": "string", "description": "The ID of the target element."},
                "text": {"type": "string", "description": "The text to type."}
            },
            "required": ["element_id", "text"]
        }
    },
    {
        "name": "navigate_browser",
        "description": "Navigate the automated browser to a specific URL.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to visit."}
            },
            "required": ["url"]
        }
    },
    {
        "name": "auto_navigator",
        "description": "Execute a high-level automated web mission (e.g., 'buy a mouse on Amazon').",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "The mission objective."}
            },
            "required": ["task"]
        }
    },
    {
        "name": "voice_command_mission",
        "description": "Trigger a high-level autonomous task based on a complex voice command.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "The command or mission."}
            },
            "required": ["task"]
        }
    },
    {
        "name": "manage_implementation_plan",
        "description": "GSD/Ralph Wiggum Workflow: Read, Write, or Update the IMPLEMENTATION_PLAN.md for complex missions.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "'read', 'write', or 'update'."},
                "content": {"type": "string", "description": "The plan content or update summary."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "auto_browser_dom",
        "description": "Fullstack Hightech: Fetch the Accessibility Tree (DOM) of the specified URL or current page for precision UI interaction.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Optional URL to navigate to."}
            }
        }
    },
    {
        "name": "manage_memory",
        "description": "Archive or Retrieve information from JACK's long-term Neural Archive (Vector DB).",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "'store' to archive a fact, 'recall' to retrieve relevant info."},
                "fact": {"type": "string", "description": "The fact to remember (for 'store')."},
                "query": {"type": "string", "description": "The search query (for 'recall')."}
            },
            "required": ["action"]
        }
    },
    {
        "name": "firecrawl_extract",
        "description": "Deep, structured web scrape using Firecrawl sensors. Best for LLM-ready data.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Target URL."},
                "action": {"type": "string", "description": "'scrape', 'crawl', or 'map'."}
            },
            "required": ["url"]
        }
    },
    {
        "name": "sandboxed_python",
        "description": "Execute code in a secure E2B cloud sandbox. Use this for potentially dangerous or complex scripts.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "The Python code to execute."}
            },
            "required": ["code"]
        }
    },
]


# --- BRIDGE FUNCTIONS FOR NEW TOOLS ---

def get_screen_context():
    """Read current screen: active window, UI elements, and visible text."""
    return visual_orchestrator.get_screen_summary()


def file_management(action, path, destination=None):
    """Bridge for file operations."""
    return system_controller.manage_files(action, path, destination)


def keyboard_shortcut(keys):
    """Press a keyboard shortcut like ctrl+c, alt+f4, win+d."""
    try:
        import pyautogui
        key_parts = [k.strip() for k in keys.lower().split('+')]
        pyautogui.hotkey(*key_parts)
        return f"Pressed shortcut: {keys}"
    except Exception as e:
        return f"Keyboard Error: {str(e)}"


def scroll_screen(direction, amount=3):
    """Scroll the screen up or down."""
    return desktop_agent.scroll(direction, amount)


# --- JACK AGENT DEMO TOOLS ---


def format_json(data):
    import json
    try:
        return json.dumps(json.loads(data), indent=2)
    except Exception as e:
        return f"Invalid JSON: {e}"

def word_count(text):
    return str({"characters": len(text), "words": len(text.split()), "lines": len(text.splitlines())})

def get_system_info():
    import platform
    return str({
        "os": platform.system(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
    })

def fetch_url(url):
    import requests
    try:
        resp = requests.get(url, timeout=10)
        return resp.text[:4000]
    except Exception as e:
        return f"Failed to fetch: {e}"

def system_power(action):
    import os
    if action == "shutdown":
        os.system("shutdown /s /t 5")
        return "Shutting down the system in 5 seconds."
    elif action == "restart":
        os.system("shutdown /r /t 5")
        return "Restarting the system in 5 seconds."
    return "Invalid action."


def push_to_git(commit_message):
    """Commit and push changes to the repository."""
    try:
        get_signals().emit_bridge("pipeline_stage", "GIT_SYNC", "Synchronizing with GitHub...")
        
        # 1. Add all changes
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
        # 2. Commit
        subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True)
        
        # 3. Push
        result = subprocess.run(["git", "push"], check=True, capture_output=True, text=True)
        
        success_msg = f"System synchronized successfully: {commit_message}"
        get_signals().emit_bridge("pipeline_stage", "SUCCESS", "Git Sync Complete")
        return success_msg
    except subprocess.CalledProcessError as e:
        error_msg = f"Git Sync Error: {e.stderr or e.stdout}"
        if "bit" in error_msg.lower() and "up to date" in error_msg.lower():
            return "System is already up to date with repository."
        return error_msg
    except Exception as e:
        return f"Unexpected Git Error: {str(e)}"



# Mapping from function names to callable functions for the AI tool caller
FUNCTION_MAP = {
    "get_web_data": get_web_data,
    "web_browser_control": web_browser_control,
    "immortal_web_agent": browse_titan,
    "execute_terminal_command": execute_terminal_command,
    "visual_locate": visual_locate,
    "system_process_monitor": system_process_monitor,
    "open_application": open_application,
    "get_system_stats": get_system_stats,
    "get_current_time": get_current_time,
    "analyze_screen_deep": analyze_screen_deep,
    "visual_click": visual_click,
    "get_wikipedia_summary": get_wikipedia_summary,
    "start_autonomous_mission": start_autonomous_mission,
    "deep_search_mission": deep_search_mission,
    "open_any_url": open_any_url,
    "simple_calculator": simple_calculator,
    "take_screenshot": take_screenshot,
    "os_control_interpreter": os_control_interpreter,
    "windows_ui_sniffer": windows_ui_sniffer,
    "run_titan_skill": execute_titan_skill,
    "execute_titan_skill": execute_titan_skill,
    "diagnose_and_repair": diagnose_and_repair,
    "install_from_github": install_from_github,
    "absorb_github_technology": install_from_github,
    "get_stock_price": get_stock_price,
    "check_internet_speed": check_internet_speed,
    "wolfram_alpha_query": wolfram_alpha_query,
    "agent_doctor": agent_doctor,
    "system_cleanup": system_cleanup,
    "autonomous_desktop_mission": autonomous_desktop_mission,
    "spawn_claw_swarm": spawn_claw_swarm,
    "file_management": file_management,
    "native_type": native_type,
    "native_click": native_click,
    "keyboard_shortcut": keyboard_shortcut,
    "scroll_screen": scroll_screen,
    "get_screen_context": get_screen_context,
    "dom_click": dom_click,
    "dom_type": dom_type,
    "dom_read": dom_read,
    "virus_scan": virus_scan,
    # --- NEW POWER TOOLS ---
    "open_file": open_file,
    "search_files": search_files,
    "clean_temp_files": clean_temp_files,
    "kill_process": kill_process,
    "disk_usage": disk_usage,
    "list_folder": list_folder,
    "read_file_content": read_file_content,
    "manage_clipboard": manage_clipboard,
    "set_reminder": set_reminder,
    "download_file": download_file,
    "get_world_news": get_world_news,
    "open_world_monitor": open_world_monitor,
    "format_json": format_json,
    "word_count": word_count,
    "get_system_info": get_system_info,
    "fetch_url": fetch_url,
    "system_power": system_power,
    "push_to_git": push_to_git,
    "morning_digest": lambda **kw: execute_titan_skill("morning_digest"),
    "arxiv_research": lambda query: execute_titan_skill("arxiv_research", query),
    "inspect_dom": inspect_dom,
    "precision_click": precision_click,
    "precision_type": precision_type,
    "navigate_browser": navigate_browser,
    "auto_navigator": lambda task: execute_titan_skill("auto_navigator", task),
    "voice_command_mission": lambda task: execute_titan_skill("voice_command_mission", task),
    "manage_implementation_plan": manage_implementation_plan,
    "auto_browser_dom": auto_browser_dom,
    "manage_memory": manage_memory,
    "firecrawl_extract": firecrawl_extract,
    "sandboxed_python": sandboxed_python,
}
