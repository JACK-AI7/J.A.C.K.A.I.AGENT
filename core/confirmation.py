import sys

def confirm_action(action_description: str):
    """
    Mandatory human-in-the-loop confirmation for dangerous actions.
    In a headless/GUI mode, this would trigger a UI popup.
    """
    print(f"\n[[WARN] SECURITY ALERT] JACK is requesting permission to:")
    print(f"👉 {action_description}")
    
    # In CLI mode
    try:
        choice = input("Confirm Action? (yes/no): ").strip().lower()
        return choice in ["yes", "y", "confirm"]
    except EOFError:
        return False # Default to safe fail

def safe_delete(file_path: str):
    """Safely delete a file after human confirmation."""
    import os
    if not os.path.exists(file_path):
        return f"Neural Error: Target '{file_path}' does not exist."
        
    if confirm_action(f"PERMANENTLY DELETE: {file_path}"):
        try:
            os.remove(file_path)
            return f"Interaction SUCCESS: {file_path} has been purged from the system."
        except Exception as e:
            return f"Purge Error: {str(e)}"
    else:
        return "Action ABORTED: Security clearance not granted by Operator."
