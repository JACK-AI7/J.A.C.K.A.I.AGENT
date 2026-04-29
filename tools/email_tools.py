import webbrowser
import urllib.parse

def open_gmail():
    """Open Gmail in the default browser."""
    webbrowser.open("https://mail.google.com")
    return "Materialized Gmail portal in browser."

def compose_email(to: str, subject: str, body: str):
    """Compose a new email using the system's mailto protocol."""
    safe_subject = urllib.parse.quote(subject)
    safe_body = urllib.parse.quote(body)
    url = f"mailto:{to}?subject={safe_subject}&body={safe_body}"
    webbrowser.open(url)
    return f"Prepared email transmission to: {to}"
