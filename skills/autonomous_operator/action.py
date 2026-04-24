import asyncio
import os
from operate.main import main as operate_main
try:
    from nexus_bridge import get_signals
except ImportError:
    class _DummySignals:
        def emit_bridge(self, *a, **kw): pass
    _signals = _DummySignals()
    def get_signals(): return _signals

async def start_operator_mission(task_description):
    """
    TITAN Autonomous Operator: Executes a visual desktop mission using Self-Operating Computer.
    Designed to work like a human operator by viewing the screen and simulating mouse/keyboard.
    """
    signals = get_signals()
    signals.thought_received.emit(f"Handing control to Visual Operator for: {task_description[:50]}...", "decision")
    
    # We run the operate loop. Self-operating-computer handles its own LLM calls (usually GPT-4V).
    # Since the user wants local first, it's worth noting to use Gemini or local Llava if supported, 
    # but the core 'operate' package is hardcoded for OpenAI/Gemini/Anthropic APIs usually.
    # We will ensure environment variables are ready.
    
    print(f"TITAN Operator: Mission Start - {task_description}")
    try:
        # In a real integration, we'd pass the task to the framework.
        # Self-operating-computer's 'main' typically enters an interactive loop or takes a --prompt.
        # Here we bridge it into the JACK environment.
        
        # Self-operating-computer works by reading the prompt from command line or its internal loop.
        # This is a high-level integration.
        
        # signals.status_updated.emit("Autonomous Operator", 10, "operator_root")
        
        # Note: This executes the main loop of the 'operate' framework.
        # In actual usage, one might run 'operate --prompt "..."' via subprocess
        import subprocess
        
        cmd = ["operate", "--prompt", task_description]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            return f"Visual Operator MISSION SUCCESS: {stdout[-500:]}"
        else:
            return f"Visual Operator Interruption: {stderr}"
            
    except Exception as e:
        return f"Autonomous Operator Error: {str(e)}"

def execute(task=None):
    """
    Entry point for the Autonomous Operator skill.
    """
    if not task:
        return "Tactical Error: No mission manifest for Autonomous Operator."
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(start_operator_mission(task))
