import os
import re
import traceback
import json
from core.nexus_bridge import get_signals


def execute(task="diagnose", fix=False, **kwargs):
    """
    JACK TITAN: AUTO-CODER
    The self-healing core that allows JACK to identify and fix his own code.
    """
    LOG_FILE = "jack_error.log"

    if task == "diagnose":
        return diagnose_and_repair(LOG_FILE, fix=fix)
    else:
        return f"Unknown Auto-Coder task: {task}"


def diagnose_and_repair(log_path, fix=False):
    signals = get_signals()
    signals.thought_received.emit("Architect Mode: Initiating System Diagnostic...", "decision")
    print("TITAN ARCHITECT: Initiating System Diagnostic...")

    if not os.path.exists(log_path):
        signals.thought_received.emit("System Scan: 100% Integrity. No anomalies detected.", "thought")
        return "System Healthy: No error logs found."

    # 1. Read the last few lines of the error log
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
            if not lines:
                return "System Healthy: Logs are empty."

            # Find the last FATAL or ERROR trace
            error_msg = lines[-1].strip()
            print(f"TITAN ARCHITECT: Found Lead - {error_msg}")
    except Exception as e:
        return f"Architect Error: Failed to read logs ({e})"

    # 2. Heuristic: Look for a file path and line number in the message
    # Pattern like "C:\...\main.py", line 53
    match = re.search(r'file "(.*?)", line (\d+)', error_msg.lower())
    if not match:
        # Fallback: Just return the error for the AI to reason about
        return f"I found a recent error in my logs: '{error_msg}'. Please tell me why this happened."

    file_path = match.group(1)
    line_number = int(match.group(2))

    # 3. Read the offending file around the line
    if not os.path.exists(file_path):
        return f"Architect Error: Offending file {file_path} no longer exists."

    try:
        with open(file_path, "r") as f:
            content = f.readlines()

        start = max(0, line_number - 10)
        end = min(len(content), line_number + 10)
        snippet = "".join(content[start:end])

        analysis = (
            f"TITAN ARCHITECT SUMMARY:\n"
            f"- Error detected in: {os.path.basename(file_path)}\n"
            f"- Critical Line: {line_number}\n"
            f"- Error Message: {error_msg}\n"
            f"\nCODE SNIPPET:\n{snippet}\n"
        )

        if fix:
            signals.thought_received.emit(f"Critial Failure found in {os.path.basename(file_path)}. Applying Patch...", "decision")
            analysis += (
                "Sir, I have analyzed my failure. I am ready to apply a patch to "
                + os.path.basename(file_path)
                + "."
            )
            # Attempt to fix the error
            success, patch = generate_fix(file_path, line_number, error_msg, snippet)
            if success:
                signals.thought_received.emit("Success: Patch applied. Integrity Restored.", "thought")
                analysis += f"\n\nPATCH APPLIED:\n{patch}"
            else:
                signals.thought_received.emit(f"Hardware Failure: {patch}", "log")
                analysis += f"\n\nCould not generate a fix. Error: {patch}"
        else:
            analysis += (
                "\nSir, I have analyzed my failure. I am ready to apply a patch to "
                + os.path.basename(file_path)
                + ". Use the 'fix' parameter to apply it."
            )

        return analysis

    except Exception as e:
        return f"Architect Error: Failed to analyze source code ({e})"


def generate_fix(file_path, line_number, error_msg, snippet):
    """Attempt to generate and apply a fix for the error."""
    try:
        # Simple heuristic fixes based on common errors
        if "name 'os' is not defined" in error_msg:
            # Add import os at the top
            with open(file_path, "r") as f:
                lines = f.readlines()

            # Insert import os at the top if not present
            if lines and "import os" not in [l.strip() for l in lines[:10]]:
                lines.insert(0, "import os\n")
                with open(file_path, "w") as f:
                    f.writelines(lines)
                return True, "Added missing 'import os' at the top of the file."

        if "name 're' is not defined" in error_msg:
            # Add import re at the top
            with open(file_path, "r") as f:
                lines = f.readlines()

            if lines and "import re" not in [l.strip() for l in lines[:10]]:
                lines.insert(0, "import re\n")
                with open(file_path, "w") as f:
                    f.writelines(lines)
                return True, "Added missing 'import re' at the top of the file."

        # Add more fix heuristics as needed
        return False, "No automatic fix available for this error type."

    except Exception as e:
        return False, f"Error generating fix: {e}"


if __name__ == "__main__":
    print(execute("diagnose"))
