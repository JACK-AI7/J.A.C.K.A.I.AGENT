import os
import sys
from typing import Optional, Dict, Any
from core.logger import log_event

class CommandProcessor:
    """The Slash Command Engine for J.A.C.K.A.I.AGENT, inspired by Hermes Agent."""
    
    def __init__(self, agent):
        self.agent = agent
        self.commands = {
            "/skills": self.list_skills,
            "/status": self.get_status,
            "/platforms": self.list_platforms,
            "/stop": self.stop_work,
            "/sethome": self.set_home,
            "/clear": self.clear_screen,
        }

    def process(self, text: str) -> Optional[str]:
        """Process a command if it starts with '/'. Returns response or None."""
        text = text.strip()
        if not text.startswith("/"):
            return None
            
        parts = text.split()
        cmd = parts[0].lower()
        args = parts[1:]
        
        # Handle registered commands
        if cmd in self.commands:
            return self.commands[cmd](args)
            
        # Handle /<skill-name> shorthand
        skill_name = cmd[1:]
        if self._is_valid_skill(skill_name):
            return self.run_skill(skill_name, " ".join(args))
            
        return f"Unknown command: {cmd}. Type /skills to see available tools."

    def list_skills(self, args) -> str:
        """List all available neural skills."""
        skills_dir = "skills"
        if not os.path.exists(skills_dir):
            return "No skills found in the system, Sir."
            
        skills = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d))]
        return "### NEURAL SKILLS DIRECTORY:\n" + "\n".join([f"- /{s}" for s in skills])

    def get_status(self, args) -> str:
        """Get high-level system status."""
        from core.tools import get_system_stats
        stats = get_system_stats()
        return f"### SYSTEM STATUS:\n- Mode: {self.agent.mode}\n- {stats}"

    def list_platforms(self, args) -> str:
        """List active communication gateways."""
        if hasattr(self.agent, "gateway"):
            active = list(self.agent.gateway.bridges.keys())
            return f"### ACTIVE GATEWAYS:\n- " + "\n- ".join(active) if active else "No active external gateways."
        return "Gateway engine is offline, Sir."

    def stop_work(self, args) -> str:
        """Interrupt current work loop."""
        # This is handled by setting a flag in the loop
        self.agent.loop.interrupt = True
        return "Neural interrupt signal sent. Stopping mission..."

    def set_home(self, args) -> str:
        """Set the primary workspace directory."""
        if not args:
            return f"Current home: {os.getcwd()}"
        new_home = args[0]
        if os.path.exists(new_home):
            os.chdir(new_home)
            return f"Home directory re-aligned to: {new_home}"
        return f"Error: Path '{new_home}' does not exist."

    def clear_screen(self, args) -> str:
        """Clear the CLI display."""
        os.system('cls' if os.name == 'nt' else 'clear')
        return "Neural display purged."

    def _is_valid_skill(self, skill_name: str) -> bool:
        return os.path.exists(os.path.join("skills", skill_name))

    def run_skill(self, skill_name: str, task: str) -> str:
        """Directly trigger a skill via shorthand command."""
        from tools import execute_titan_skill
        return execute_titan_skill(skill_name, task)

# Bridge helper
def process_slash_command(agent, text: str):
    if not hasattr(agent, "command_processor"):
        agent.command_processor = CommandProcessor(agent)
    return agent.command_processor.process(text)
