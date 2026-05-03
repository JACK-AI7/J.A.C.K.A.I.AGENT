"""
Dashboard Integration Hub
Connects all agents to HUD visualization
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.nexus_bridge import get_signals

# Import all agents
try:
    from agents.desktop_agent import desktop_agent as da
    DESKTOP_AGENT_AVAILABLE = True
except Exception as e:
    print(f"DesktopAgent import failed: {e}")
    DESKTOP_AGENT_AVAILABLE = False

try:
    from agents.system_controller import system_controller as sc
    SYSTEM_CONTROLLER_AVAILABLE = True
except Exception as e:
    print(f"SystemController import failed: {e}")
    SYSTEM_CONTROLLER_AVAILABLE = False

try:
    from agents.visual_orchestrator import VisualOrchestrator
    VISUAL_ORCHESTRATOR_AVAILABLE = True
except Exception as e:
    print(f"VisualOrchestrator import failed: {e}")
    VISUAL_ORCHESTRATOR_AVAILABLE = False

try:
    from agents.web_navigator import web_navigator as wn
    WEB_NAVIGATOR_AVAILABLE = True
except Exception as e:
    print(f"WebNavigator import failed: {e}")
    WEB_NAVIGATOR_AVAILABLE = False


class AgentDashboardManager:
    """Central manager for agent-to-HUD communication"""
    
    def __init__(self):
        self.signals = get_signals()
        self.agents_initialized = {}
        
        # Initialize all agents
        self._init_agents()
        
        # Connect signals to HUD updates
        self._connect_signals()
        
    def _init_agents(self):
        """Initialize all available agents and register them"""
        
        if DESKTOP_AGENT_AVAILABLE:
            self.agents_initialized["DesktopAgent"] = da
            # DesktopAgent already emits init signal
            
        if SYSTEM_CONTROLLER_AVAILABLE:
            self.agents_initialized["SystemController"] = sc
            
        if VISUAL_ORCHESTRATOR_AVAILABLE:
            self.agents_initialized["VisualOrchestrator"] = VisualOrchestrator()
            
        if WEB_NAVIGATOR_AVAILABLE:
            self.agents_initialized["WebNavigator"] = wn
            
        print(f"[Dashboard] Registered {len(self.agents_initialized)} agents")
        
    def _connect_signals(self):
        """Connect agent signals to HUD visualization"""
        # Agent status, action, thought signals are already connected through nexus_bridge
        # The HUDManager connects to these signals directly
        pass
        
    def get_agent(self, name):
        """Get an initialized agent by name"""
        return self.agents_initialized.get(name)
        
    def list_agents(self):
        """List all available agents"""
        return list(self.agents_initialized.keys())


# Singleton instance
dashboard_manager = AgentDashboardManager()
