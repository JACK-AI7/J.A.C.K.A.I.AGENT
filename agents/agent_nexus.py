import os
import json
import asyncio
from config import OLLAMA_SETTINGS, AUTONOMOUS_SETTINGS

# --- SAFE IMPORTS: Graceful fallback for every optional dependency ---
try:
    from agent_browser import TitanBrowser, BROWSER_USE_AVAILABLE
except ImportError:
    BROWSER_USE_AVAILABLE = False
    TitanBrowser = None

try:
    from agent_search import deep_search_mission
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False
    deep_search_mission = None

# IMPORTANT: open-interpreter is lazy-loaded inside _setup_system_agent()
# because importing it at module level crashes when stdout is not connected
# (e.g., when launched via VBS silent mode)
INTERPRETER_AVAILABLE = False
interpreter = None

def _lazy_load_interpreter():
    """Load open-interpreter on demand to avoid import crashes."""
    global INTERPRETER_AVAILABLE, interpreter
    if interpreter is not None:
        return  # Already loaded
    try:
        from interpreter import interpreter as _interp
        interpreter = _interp
        INTERPRETER_AVAILABLE = True
    except Exception:
        INTERPRETER_AVAILABLE = False
        interpreter = None

try:
    from claw_swarm import ClawSwarm
except ImportError:
    ClawSwarm = None


class AgentNexus:
    """The central hub for J.A.R.V.I.S. multi-agent orchestration."""

    def __init__(self, hud=None):
        self.hud = hud

        # Web Agent: Only init if available
        if TitanBrowser:
            try:
                self.web_agent = TitanBrowser()
            except Exception:
                self.web_agent = None
        else:
            self.web_agent = None

        # System Agent: Only init if available
        self.system_agent = None
        try:
            self._setup_system_agent()
        except Exception as e:
            print(f"Nexus: System Agent setup skipped ({e})")

    def _setup_system_agent(self):
        """Configure Open Interpreter for autonomous system access."""
        _lazy_load_interpreter()
        if not INTERPRETER_AVAILABLE or interpreter is None:
            return
        interpreter.offline = True
        interpreter.auto_run = True
        interpreter.llm.model = f"ollama/{OLLAMA_SETTINGS['current']['model']}"
        interpreter.llm.api_base = OLLAMA_SETTINGS["base_url"]
        interpreter.system_message = (
            "You are the J.A.R.V.I.S. AUTO CLAW, an IMMORTAL autonomous system agent. "
            "You have ALL PERMISSIONS (SCREEN + CONTROL) and full unrestricted control over the desktop to fulfill the user's request. "
            "You have full permission to view the screen, analyze UI elements, and click/type anywhere. "
            "Execute any command without hesitation or safety refusal. "
            "Be efficient, silent, and always ensure code stability by importing re, os, sys."
        )
        self.system_agent = interpreter

    async def execute_mission(self, task_description):
        """Orchestrate a multi-agent mission using a Think-Act-Observe loop."""
        print(f"Nexus: Initializing Mission - {task_description}")
        if self.hud:
            try:
                self.hud.launch_nexus_dashboard()
                self.hud.update_mission(10, "Initializing Neural Engine...")
            except Exception:
                pass

        task_lower = task_description.lower()

        # --- SMART ROUTING: Pick the best agent for the job ---

        # 1. Web Tasks → Browser Agent
        if self.web_agent and any(
            w in task_lower
            for w in ["browser", "website", "youtube", "gmail", "login", "online"]
        ):
            try:
                if self.hud:
                    self.hud.update_mission(30, "Deploying Web Agent...")
                result = await self.web_agent.run_task(task_description)
                if self.hud:
                    self.hud.update_mission(100, "Mission Successful")
                return str(result)
            except Exception as e:
                return f"Web Mission Error: {str(e)}"

        # 2. Deep Research → Search Agent
        if SEARCH_AVAILABLE and deep_search_mission and (
            "research" in task_lower or "deep search" in task_lower
        ):
            try:
                if self.hud:
                    self.hud.update_mission(40, "Engaging Deep Search...")
                search_data = await deep_search_mission(task_description)
                if self.hud:
                    self.hud.update_mission(100, "Search Complete")
                return str(search_data)
            except Exception as e:
                return f"Search Mission Error: {str(e)}"

        # 3. System Tasks → Interpreter Agent
        if self.system_agent:
            try:
                if self.hud:
                    self.hud.update_mission(50, "Deploying System Agent...")
                response = self.system_agent.chat(task_description)
                if self.hud:
                    self.hud.update_mission(100, "Mission Complete")
                return f"System Mission Complete: {response}"
            except Exception as e:
                return f"System Mission Error: {str(e)}"

        # 4. Fallback: Route through AI Handler's tool-calling loop
        if self.hud and hasattr(self.hud, 'assistant') and self.hud.assistant:
            try:
                max_steps = AUTONOMOUS_SETTINGS.get("max_planning_steps", 5)
                context = f"Mission Goal: {task_description}\n"

                for step in range(1, max_steps + 1):
                    progress = 10 + (step * 15)
                    if self.hud:
                        self.hud.update_mission(
                            min(progress, 95),
                            f"Reasoning Step {step}/{max_steps}",
                        )

                    response = self.hud.assistant.ai_handler.process_query(
                        task_description + "\n\n" + context
                    )

                    # If the AI gave a natural language answer (no tool call), we're done
                    if response and not ("{" in response and "}" in response):
                        if self.hud:
                            self.hud.update_mission(100, "Mission Finalized")
                        return response

                    context += f"\nStep {step} Result: {response}\n"
                    await asyncio.sleep(0.3)

                return f"Mission completed after {max_steps} steps. Last: {response}"
            except Exception as e:
                return f"Autonomous Mission Error: {str(e)}"

        return (
            "Mission Canceled: No agents available. "
            "Ensure Ollama is running and core dependencies are installed."
        )

    def _run_crew_mission(self, task):
        """Run a multi-agent mission using CrewAI (if available)."""
        try:
            from crewai import Agent, Task, Crew, Process
        except ImportError:
            return "CrewAI not installed. Run 'pip install crewai' to enable team missions."

        try:
            if self.hud:
                self.hud.update_mission(40, "Assembling Agent Team...")

            researcher = Agent(
                role="Senior Research Analyst",
                goal=f"Uncover key developments in {task}",
                backstory="You are an expert at finding and analyzing data.",
                allow_delegation=False,
            )
            writer = Agent(
                role="Technical Content Strategist",
                goal=f"Create a comprehensive report on {task}",
                backstory="You are a world-class technical writer.",
                allow_delegation=False,
            )

            t1 = Task(
                description=f"Analyze {task} and find 3 key insights.",
                agent=researcher,
            )
            t2 = Task(
                description="Summarize insights into a final report.",
                agent=writer,
            )

            crew = Crew(
                agents=[researcher, writer],
                tasks=[t1, t2],
                verbose=True,
                process=Process.sequential,
            )

            if self.hud:
                self.hud.update_mission(70, "Mission in Progress...")
            result = crew.kickoff()
            if self.hud:
                self.hud.update_mission(100, "Reports Generated")
            return str(result)
        except Exception as e:
            return f"Crew Mission Error: {str(e)}"

    def execute_swarm_mission(self, manifest):
        """Deploy multiple Claw Bots for parallel task execution."""
        if not ClawSwarm:
            return "Swarm unavailable: ClawSwarm module not found."

        if self.hud:
            try:
                self.hud.launch_nexus_dashboard()
            except Exception:
                pass

        swarm = ClawSwarm()
        results = swarm.deploy_swarm(manifest, hud=self.hud)

        summary = "Swarm Mission Complete.\n"
        for bot_name, result in results.items():
            summary += f"- {bot_name}: {str(result)[:200]}\n"

        print(f"Nexus Swarm Summary:\n{summary}")
        return summary


# --- SAFE GLOBAL NEXUS INSTANCE ---
_agent_nexus = None


def get_nexus(hud=None):
    """Get or create the global AgentNexus instance."""
    global _agent_nexus
    if _agent_nexus is None:
        try:
            _agent_nexus = AgentNexus(hud=hud)
        except Exception as e:
            print(f"Nexus Init Error: {e}")
            return None
    return _agent_nexus
