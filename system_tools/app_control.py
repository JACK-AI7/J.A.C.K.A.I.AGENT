import subprocess
import platform
import os

def open_app(name: str):
    """Reliably open or focus an application based on the host OS."""
    system = platform.system()

    try:
        if system == "Windows":
            # Use 'start' to open applications or URLs
            return subprocess.Popen(["start", "", name], shell=True)
        elif system == "Darwin":  # macOS
            return subprocess.Popen(["open", "-a", name])
        else:  # Linux
            return subprocess.Popen([name])
    except Exception as e:
        return f"Neural Error: Failed to materialize application '{name}' - {str(e)}"

def open_email_client():
    """Open the system default email client."""
    system = platform.system()
    try:
        if system == "Windows":
            return subprocess.Popen(["start", "mailto:"], shell=True)
        elif system == "Darwin":
            return subprocess.Popen(["open", "mailto:"])
        else:
            return subprocess.Popen(["xdg-open", "mailto:"])
    except Exception as e:
        return f"Neural Error: Failed to engage email uplink - {str(e)}"
