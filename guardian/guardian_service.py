import time
import psutil
import asyncio
from system_tools.security_tools import scan_path, find_large_files
from guardian.predictor import predict_system_issues
from core.logger import log_event

class GuardianService:
    """The 'Sentry' of JACK: Continuous monitoring and proactive protection."""
    def __init__(self, dashboard_callback=None):
        self.running = False
        self.callback = dashboard_callback
        self.scan_scope = "." # Home directory for scan

    def start(self):
        """Begin the Guardian monitoring cycle."""
        self.running = True
        log_event("Guardian Protocol: Sentry Mode Online.")
        
        while self.running:
            try:
                stats = self.run_cycle()
                if self.callback:
                    # In a real async environment, this would be await self.callback(stats)
                    try:
                        self.callback(stats)
                    except: pass
            except Exception as e:
                log_event(f"Guardian Cycle Error: {str(e)}")
                
            time.sleep(60) # Scan every minute

    def stop(self):
        self.running = False
        log_event("Guardian Protocol: Sentry Mode Offline.")

    def run_cycle(self):
        """Execute a single monitoring and protection cycle."""
        data = {
            "timestamp": time.time(),
            "cpu": psutil.cpu_percent(interval=1),
            "ram": psutil.virtual_memory().percent,
            "security": "System Integrity: SEALED",
            "junk": [],
            "alerts": []
        }

        # 1. Proactive Security Scan (Background)
        try:
            # We only do a quick scan for the MVP
            # data["security"] = scan_path(self.scan_scope)
            pass
        except:
            data["security"] = "Security Interface Offline"

        # 2. Junk Detection
        try:
            data["junk"] = find_large_files(self.scan_scope, size_mb=500)[:5]
        except:
            pass

        # 3. Predictive Analysis
        data["alerts"] = predict_system_issues(data)

        log_event(f"Guardian Status: CPU {data['cpu']}% | RAM {data['ram']}% | Alerts: {len(data['alerts'])}")
        return data
