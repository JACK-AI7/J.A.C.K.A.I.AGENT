import webbrowser
import urllib.parse

# Initialize Nexus Bridge signals
try:
    from core.nexus_bridge import get_signals
    signals = get_signals()
except:
    signals = None


def open_gmail():
    """Open Gmail in the default browser."""
    try:
        if signals:
            signals.emit_bridge("agent_action", "EmailTools", "OPEN", "Opening Gmail")
            signals.emit_bridge("agent_status", "EmailTools", "ACTIVE", "Gmail portal")
    except:
        pass
        
    webbrowser.open("https://mail.google.com")
    return "Materialized Gmail portal in browser."


def compose_email(to: str, subject: str, body: str):
    """Compose a new email using the system's mailto protocol."""
    try:
        safe_subject = urllib.parse.quote(subject)
        safe_body = urllib.parse.quote(body)
        url = f"mailto:{to}?subject={safe_subject}&body={safe_body}"
        
        webbrowser.open(url)
        
        result = f"Prepared email transmission to: {to}"
        
        if signals:
            signals.emit_bridge("agent_action", "EmailTools", "COMPOSE", f"To: {to}, Subject: {subject[:30]}...")
            signals.emit_bridge("agent_status", "EmailTools", "ACTIVE", "Email compose window")
            
        return result
    except Exception as e:
        if signals:
            signals.emit_bridge("agent_action", "EmailTools", "COMPOSE", f"Error: {str(e)}")
        return f"Email compose failed: {str(e)}"
