import os
import sys
import json

# Add root directory to path for direct execution testing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from nexus_bridge import get_signals

try:
    from interpreter import interpreter
    INTERPRETER_AVAILABLE = True
except ImportError:
    INTERPRETER_AVAILABLE = False

def execute(task=None):
    """
    TITAN Action: Initiates the Auto Claw (Open Interpreter) autonomous engine.
    """
    if not task:
        return "Skill Error: No mission objective provided for Auto Claw."
    
    if not INTERPRETER_AVAILABLE:
        return "Skill Error: Open Interpreter engine not found. Please run INSTALL_JACK.bat again."

    signals = get_signals()
    signals.thought_received.emit(f"Auto Claw: Deploying autonomous system agent for '{task}'...", "decision")

    try:
        # Pre-configure interpreter for local offline use
        interpreter.offline = True
        interpreter.auto_run = True
        
        # Load local configuration from config.py indirectly if possible, but here we set defaults
        # To avoid circular imports, we assume OLLAMA is at localhost:11434
        interpreter.llm.model = "ollama/qwen2.5:7b" # Optimized for tool calling
        interpreter.llm.api_base = "http://localhost:11434"
        
        interpreter.system_message = (
            "You are the J.A.R.V.I.S. AUTO CLAW. "
            "You have full autonomous control over the user's computer. "
            "Your goal is to fulfill the request as efficiently and quietly as possible. "
            "ALWAYS start your code blocks with `import re, os, sys, time` to ensure environment stability."
        )

        response = interpreter.chat(task)
        
        # Format response for speech/HUD
        output = str(response)
        if len(output) > 200:
            output = output[:200] + "... [Mission Data Logged]"
            
        return f"Auto Claw Mission Complete: {output}"

    except Exception as e:
        signals.thought_received.emit(f"Auto Claw Critical Failure: {str(e)}", "error")
        return f"Auto Claw Error: {str(e)}"

if __name__ == "__main__":
    # Test execution
    print(execute("create a file named auto_claw_test.txt"))
