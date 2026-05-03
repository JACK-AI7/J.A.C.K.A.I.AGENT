import os
import sys
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# Add root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Initialize Nexus Bridge signals
try:
    from core.nexus_bridge import get_signals
    signals = get_signals()
except:
    signals = None

# Initialize Nexus Bridge signals
try:
    from core.nexus_bridge import get_signals
    signals = get_signals()
except:
    signals = None

class MessagingService:
    def __init__(self):
        self.driver = None
        self.contacts_file = os.path.join(os.path.dirname(__file__), "contacts.json")
        self._ensure_contacts()
        
        # Emit initialization signal
        try:
            from core.nexus_bridge import get_signals
            self.signals = get_signals()
            self.signals.emit_bridge("agent_status", "WhatsAppSkill", "INITIALIZED", "Messaging service ready")
        except:
            self.signals = None
        
        # Emit initialization signal
        try:
            from core.nexus_bridge import get_signals
            self.signals = get_signals()
            self.signals.emit_bridge("agent_status", "WhatsAppSkill", "INITIALIZED", "Messaging service ready")
        except:
            self.signals = None

    def _ensure_contacts(self):
        if not os.path.exists(self.contacts_file):
            with open(self.contacts_file, 'w', encoding='utf-8') as f:
                json.dump({"mom": "+1234567890", "dad": "+1234567891"}, f, indent=2)

    def _load_contacts(self):
        with open(self.contacts_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_driver(self):
        if self.driver:
            try:
                _ = self.driver.current_url
                return self.driver
            except:
                self.driver.quit()
                self.driver = None

        print("Messaging System: Initializing Chrome Engine (WhatsApp Node)...")
        chrome_options = Options()
        # Use a persistent user profile if possible to avoid re-scanning QR code
        user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'JACK_WhatsApp_Profile')
        chrome_options.add_argument(f"user-data-dir={user_data_dir}")
        
        # On Windows, we need to handle paths carefully
        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            self.driver.maximize_window()
            return self.driver
        except Exception as e:
            print(f"Driver Initialization Failed: {e}")
            return None

    def send_whatsapp(self, recipient, message):
        """Send a WhatsApp message using WhatsApp Web"""
        try:
            # Emit action start
            if hasattr(self, 'signals') and self.signals:
                self.signals.emit_bridge("agent_action", "WhatsAppSkill", "SEND", f"To {recipient}: {message[:30]}...")
                self.signals.emit_bridge("agent_status", "WhatsAppSkill", "ACTIVE", "Sending WhatsApp message")
            
            contacts = self._load_contacts()
            phone = contacts.get(recipient.lower().strip(), recipient)
            
            # Clean phone number (remove non-digits except +)
            phone = "".join([c for c in phone if c.isdigit() or c == '+'])
            
            driver = self._get_driver()
            if not driver:
                result = "Messaging Error: Unable to initialize Chrome driver."
                if hasattr(self, 'signals') and self.signals:
                    self.signals.emit_bridge("agent_action", "WhatsAppSkill", "SEND", result)
                return result

            try:
                url = f"https://web.whatsapp.com/send?phone={phone}&text={message}"
                driver.get(url)
                
                wait = WebDriverWait(driver, 45) # Long wait for QR scan if needed
                
                # Wait for send button or text box
                send_btn_xpath = '//span[@data-icon="send"]'
                
                print(f"Waiting for WhatsApp Web to transmit to {phone}...")
                send_btn = wait.until(EC.element_to_be_clickable((By.XPATH, send_btn_xpath)))
                send_btn.click()
                
                time.sleep(2) # Wait for message to actually leave
                result = f"Messaging SUCCESS: Transmitted target payload to {recipient} ({phone})."
                
                # Emit success
                if hasattr(self, 'signals') and self.signals:
                    self.signals.emit_bridge("agent_action", "WhatsAppSkill", "SEND", result)
                    self.signals.emit_bridge("agent_status", "WhatsAppSkill", "ACTIVE", "Message sent")
                    
                return result
            except Exception as e:
                result = f"Messaging Failure: Transmission intercepted or timed out. Error: {str(e)}"
                if hasattr(self, 'signals') and self.signals:
                    self.signals.emit_bridge("agent_action", "WhatsAppSkill", "SEND", result)
                return result
        except Exception as e:
            return f"Messaging Error: {str(e)}"

    def send_telegram(self, message):
        return "Telegram Bridge: Error - Bot Token not configured in .env. Portal remains closed."

    def send_discord(self, message):
        return "Discord Bridge: Error - Webhook/Token not found. Uplink unstable."

def execute(task=None):
    if not task:
        return "Messaging Error: No transmission parameters provided."

    service = MessagingService()
    task_lower = task.lower().strip()

    if "whatsapp" in task_lower:
        # Format: whatsapp [recipient] : [message]
        content = task[8:].strip()
        if ":" in content:
            recipient, message = content.split(":", 1)
            return service.send_whatsapp(recipient.strip(), message.strip())
        else:
            return "Messaging Error: Format must be 'whatsapp recipient : message'"
            
    elif "telegram" in task_lower:
        return service.send_telegram(task)
        
    elif "discord" in task_lower:
        return service.send_discord(task)
        
    else:
        return f"Messaging Error: Protocol '{task}' not recognized by the nexus."

if __name__ == "__main__":
    # Test
    # print(execute("whatsapp mom : Hello from JACK"))
    pass
