import smtplib
import imaplib
from email.message import EmailMessage
import os

def execute(task=None):
    """
    Sends or reads email (stubs for protocol).
    Task format: 'send: to:[email] | subject:[subj] | body:[text]'
    """
    if not task:
        return "Email Ops Error: No task provided."
    
    # This is a template for the user to configure their local SMTP/IMAP settings
    # In a real scenario, these would come from .env
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    email_user = os.getenv("EMAIL_USER", "")
    email_pass = os.getenv("EMAIL_PASS", "")

    if task.startswith("send:"):
        if not email_user or not email_pass:
            return "Email Ops Error: EMAIL_USER/EMAIL_PASS not configured in .env."
        
        try:
            # Parse simple format
            parts = task.replace("send:", "").split("|")
            to_email = ""
            subject = ""
            body = ""
            for p in parts:
                if "to:" in p: to_email = p.replace("to:", "").strip()
                if "subject:" in p: subject = p.replace("subject:", "").strip()
                if "body:" in p: body = p.replace("body:", "").strip()
            
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = email_user
            msg['To'] = to_email
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email_user, email_pass)
                server.send_message(msg)
            
            return f"Email sent successfully to {to_email}."
        except Exception as e:
            return f"SMTP Error: {str(e)}"
            
    elif task.startswith("check"):
        return "IMAP Check stub: Configure IMAP settings in .env to enable reading emails."
    else:
        return "Email Ops Error: Unknown command. Use 'send:' or 'check'."
