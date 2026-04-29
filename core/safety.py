BLOCKED_COMMANDS = [
    "rm -rf",
    "shutdown",
    "format",
    "del /s",
    "rd /s",
    "mkfs",
    "dd if=",
]

def is_safe(command: str):
    """Safety guard to prevent destructive system commands."""
    cmd_lower = command.lower()
    for bad in BLOCKED_COMMANDS:
        if bad in cmd_lower:
            return False
    return True
