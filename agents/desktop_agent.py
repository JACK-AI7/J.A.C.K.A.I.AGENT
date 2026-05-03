import subprocess
import os
import platform
import time
import random
import pyautogui
from PIL import Image
import psutil
from utils.humanized_input import HumanizedInput, HumanConfig


class DesktopAgent:
    def __init__(self):
        from core.config import DESKTOP_SETTINGS
        self.system = platform.system()
        
        # Create humanized input with ultra-realistic settings
        human_config = HumanConfig(
            mouse_speed_factor=1.0,
            mouse_precision=0.88,
            movement_profile=HumanConfig.movement_profile if hasattr(HumanConfig, 'movement_profile') else None,
            typing_speed_base=0.08,
            typo_chance=0.015,
            enable_verification=True
        )
        self.human = HumanizedInput(human_config)
        
        # Initialize Nexus Bridge signals for agent status
        try:
            from core.nexus_bridge import get_signals
            self.signals = get_signals()
            self.signals.emit_bridge("agent_status", "DesktopAgent", "INITIALIZED", "Ready for automation")
        except Exception as e:
            print(f"Agent signals init failed: {e}")
    
    def open_application(self, app_name):
        """Open an application by name."""
        try:
            # Emit action start
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "OPEN", f"Launching {app_name}")
            except: pass
            
            if self.system == "Darwin":  # macOS
                app_mapping = {
                    "chrome": "Google Chrome",
                    "safari": "Safari",
                    "firefox": "Firefox",
                    "spotify": "Spotify",
                    "terminal": "Terminal",
                    "finder": "Finder",
                }
                app_name_lower = app_name.lower()
                actual_app_name = app_mapping.get(app_name_lower, app_name)
                subprocess.run(["open", "-a", actual_app_name])
                result = f"At your command, Sir. Initializing {actual_app_name}."
                
            elif self.system == "Windows":
                app_mapping = {
                    "chrome": "chrome.exe",
                    "edge": "msedge.exe",
                    "firefox": "firefox.exe",
                    "notepad": "notepad.exe",
                    "calc": "calc.exe",
                    "calculator": "calc.exe",
                    "explorer": "explorer.exe",
                    "cmd": "cmd.exe",
                    "powershell": "powershell.exe",
                    "vscode": "code.exe",
                    "terminal": "wt.exe",
                }
                app_name_lower = app_name.lower().strip()
                actual_app_name = app_mapping.get(app_name_lower)
                
                if actual_app_name:
                    try:
                        if actual_app_name.startswith("ms-"):
                            os.startfile(actual_app_name)
                        else:
                            try:
                                subprocess.Popen(actual_app_name)
                            except:
                                subprocess.Popen(f'start "" "{app_name}"', shell=True)
                        result = f"At your command, Sir. Materializing {app_name} on your primary screen."
                    except Exception as e:
                        result = f"Launch Error for {app_name}: {str(e)}"
                else:
                    try:
                        subprocess.Popen(app_name_lower + ".exe")
                        result = f"At your command, Sir. Launching {app_name}."
                    except FileNotFoundError:
                        try:
                            find_cmd = f"Get-Command {app_name_lower}* -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source"
                            ps_res = subprocess.check_output(["powershell", "-Command", find_cmd], text=True).strip()
                            if ps_res:
                                subprocess.Popen(ps_res)
                                result = f"At your command, Sir. Found and launching {app_name}."
                            else:
                                subprocess.Popen(f'start "" "{app_name}"', shell=True)
                                result = f"At your command, Sir. Forcing {app_name} to launch via shell."
                        except Exception:
                            result = f"Could not find application: {app_name}"
            else:
                result = f"OS not fully supported: {self.system}"
                
            # Emit success
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "OPEN", result)
                if "At your command" in result:
                    self.signals.emit_bridge("agent_status", "DesktopAgent", "ACTIVE", f"Opened {app_name}")
            except: pass
                
            return result
            
        except Exception as e:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "OPEN", f"Error: {str(e)}")
            except: pass
            return f"Could not open {app_name}: {str(e)}"
    
    def take_screenshot(self, filename=None):
        """Take a screenshot of the entire screen."""
        try:
            if filename is None:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            self.human.capture_screen_to_file(filename)
            result = f"Screenshot saved as {filename}"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "SCREENSHOT", result)
            except: pass
            
            return result
        except Exception as e:
            return f"Could not take screenshot: {str(e)}"
    
    def click_position(self, x, y):
        """Click at specific coordinates with human-like movement."""
        try:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "CLICK", f"Moving to ({x}, {y})")
            except: pass
            
            self.human.click(x, y)
            result = f"Clicked at position ({x}, {y})"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "CLICK", result)
            except: pass
            
            return result
        except Exception as e:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "CLICK", f"Error: {str(e)}")
            except: pass
            return f"Could not click at position ({x}, {y}): {str(e)}"
    
    def type_text(self, text):
        """Type text at current cursor position with human-like keystrokes."""
        try:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "TYPE", f"Typing: {text[:30]}...")
            except: pass
            
            self.human.type_text(text)
            result = f"Typed: {text}"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "TYPE", result)
            except: pass
            
            return result
        except Exception as e:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "TYPE", f"Error: {str(e)}")
            except: pass
            return f"Could not type text: {str(e)}"
    
    def press_key(self, key):
        """Press a specific key with human-like timing."""
        try:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "KEY", f"Pressing {key}")
            except: pass
            
            self.human.press_key(key)
            result = f"Pressed key: {key}"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "KEY", result)
            except: pass
            
            return result
        except Exception as e:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "KEY", f"Error: {str(e)}")
            except: pass
            return f"Could not press key {key}: {str(e)}"
    
    def get_screen_size(self):
        """Get screen dimensions."""
        try:
            width, height = pyautogui.size()
            result = f"Screen size: {width}x{height} pixels"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "QUERY", result)
            except: pass
            
            return result
        except Exception as e:
            return f"Could not get screen size: {str(e)}"
    
    def get_mouse_position(self):
        """Get current mouse position."""
        try:
            x, y = pyautogui.position()
            result = f"Mouse position: ({x}, {y})"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "QUERY", result)
            except: pass
            
            return result
        except Exception as e:
            return f"Could not get mouse position: {str(e)}"
    
    def scroll(self, direction, amount=3):
        """Scroll up or down with human-like variable motion."""
        try:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "SCROLL", f"Scrolling {direction} {amount}")
            except: pass
            
            self.human.scroll(amount, direction)
            result = f"Scrolled {direction} {amount} units"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "SCROLL", result)
            except: pass
            
            return result
        except Exception as e:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "SCROLL", f"Error: {str(e)}")
            except: pass
            return f"Could not scroll: {str(e)}"
    
    def close_active_window(self):
        """Close the currently active window."""
        try:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "CLOSE", "Closing active window")
            except: pass
            
            if self.system == "Darwin":
                self.human.hotkey('cmd', 'w')
            elif self.system == "Windows":
                self.human.hotkey('alt', 'f4')
            elif self.system == "Linux":
                self.human.hotkey('ctrl', 'w')
                
            result = "Closed active window"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "CLOSE", result)
            except: pass
            
            return result
        except Exception as e:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "CLOSE", f"Error: {str(e)}")
            except: pass
            return f"Could not close window: {str(e)}"
    
    def minimize_window(self):
        """Minimize the currently active window."""
        try:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "MINIMIZE", "Minimizing window")
            except: pass
            
            if self.system == "Darwin":
                self.human.hotkey('cmd', 'm')
            elif self.system == "Windows":
                self.human.hotkey('win', 'down')
            elif self.system == "Linux":
                self.human.hotkey('ctrl', 'super', 'down')
                
            result = "Minimized active window"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "MINIMIZE", result)
            except: pass
            
            return result
        except Exception as e:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "MINIMIZE", f"Error: {str(e)}")
            except: pass
            return f"Could not minimize window: {str(e)}"
    
    def get_running_apps(self):
        """Get list of currently running applications."""
        try:
            running_apps = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    running_apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            unique_apps = list(set(running_apps))[:10]
            result = f"Running apps: {', '.join(unique_apps)}"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "QUERY", result)
            except: pass
            
            return result
        except Exception as e:
            return f"Could not get running apps: {str(e)}"
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard using human-like typing."""
        try:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "CLIPBOARD", f"Copying: {text[:20]}...")
            except: pass
            
            if self.system == "Darwin":
                self.human.hotkey('cmd', 'a')
            elif self.system == "Windows":
                self.human.hotkey('ctrl', 'a')
            elif self.system == "Linux":
                self.human.hotkey('ctrl', 'a')
                
            time.sleep(random.uniform(0.1, 0.3))
            self.human.type_text(text)
            result = f"Copied '{text}' to clipboard"
            
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "CLIPBOARD", result)
            except: pass
            
            return result
        except Exception as e:
            try:
                self.signals.emit_bridge("agent_action", "DesktopAgent", "CLIPBOARD", f"Error: {str(e)}")
            except: pass
            return f"Could not copy to clipboard: {str(e)}"


# Singleton Instance
desktop_agent = DesktopAgent()
