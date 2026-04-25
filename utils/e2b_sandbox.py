import os
from e2b_code_interpreter import Sandbox

def run_isolated_code(code: str):
    """Executes code in a secure E2B cloud sandbox."""
    api_key = os.getenv("E2B_API_KEY")
    if not api_key:
        return "Sandbox Error: E2B_API_KEY is missing."

    try:
        print("E2B Sandbox: Provisioning secure environment...")
        with Sandbox(api_key=api_key) as sb:
            result = sb.run_code(code)
            
            output = ""
            if result.logs.stdout:
                output += "STDOUT:\n" + "\n".join(result.logs.stdout)
            if result.logs.stderr:
                output += "\nSTDERR:\n" + "\n".join(result.logs.stderr)
            if result.error:
                output += f"\nRUNTIME ERROR: {result.error}"
                
            return output or "Code executed successfully with no output."
    except Exception as e:
        return f"Sandbox Provisioning Error: {str(e)}"
