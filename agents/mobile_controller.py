#!/usr/bin/env python
"""
MobileController agent - Unified mobile device control
- WebSocket relay (via Flutter app over WiFi)
- Direct ADB control (USB or WiFi) with screen mirroring capability
- Integrates with BrowserOnlyAgent for synchronized actions
"""

import sys
import os
import time
import subprocess
import json
import threading
import base64
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

try:
    from core.nexus_bridge import get_signals
    SIGNALS = get_signals()
except:
    SIGNALS = None

# Check ADB availability
try:
    result = subprocess.run(['adb', 'version'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        ADB_AVAILABLE = True
    else:
        ADB_AVAILABLE = False
except:
    ADB_AVAILABLE = False

# Check websockets
try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except:
    WEBSOCKETS_AVAILABLE = False


class MobileController:
    """Control Android device via ADB or WebSocket relay."""
    
    def __init__(self):
        self._adb_device = None
        self._relay_connected = False
        self._relay_ws = None
        self._relay_loop = None
        self.signals = SIGNALS
        
        self._emit("INITIALIZED", "MobileController init")
    
    def _emit(self, status, msg):
        if self.signals:
            try: self.signals.emit_bridge("agent_status", "MobileController", status, msg)
            except: pass
    
    def _action(self, act, detail):
        if self.signals:
            try: self.signals.emit_bridge("agent_action", "MobileController", act, detail)
            except: pass
    
    # ==================== ADB METHODS ====================
    def adb_connect(self, device_id=None):
        """Connect to Android device via ADB (USB or WiFi)."""
        if not ADB_AVAILABLE:
            return "ERROR: ADB not installed. Install Android SDK Platform-Tools."
        
        try:
            # List devices
            result = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=10)
            lines = result.stdout.strip().split('\n')[1:]  # skip header
            devices = [l.split('\t')[0] for l in lines if '\t' in l and 'device' in l]
            
            if not devices:
                return "No devices found. Ensure USB debugging enabled and device authorized."
            
            if device_id is None:
                device_id = devices[0]
            
            # Connect to specific device
            subprocess.run(['adb', '-s', device_id, 'wait-for-device'], timeout=10)
            self._adb_device = device_id
            self._emit("ACTIVE", f"ADB connected to {device_id}")
            return f"Connected to device {device_id}"
        except Exception as e:
            return f"ADB connect error: {e}"
    
    def adb_shell(self, command):
        """Run shell command on device."""
        if not self._adb_device:
            return "No device connected"
        try:
            result = subprocess.run(['adb', '-s', self._adb_device, 'shell', command], 
                                   capture_output=True, text=True, timeout=30)
            return result.stdout or result.stderr
        except Exception as e:
            return f"ADB shell error: {e}"
    
    def adb_screencap(self):
        """Capture screenshot via ADB (returns PIL Image)."""
        if not self._adb_device:
            return None
        try:
            # Raw binary screencap
            result = subprocess.run(['adb', '-s', self._adb_device, 'exec-out', 'screencap', '-p'],
                                   capture_output=True, timeout=10)
            if result.returncode == 0:
                return Image.open(BytesIO(result.stdout))
            else:
                print(f"Screencap error: {result.stderr}")
                return None
        except Exception as e:
            print(f"Screencap failed: {e}")
            return None
    
    def adb_input_tap(self, x, y):
        """Tap screen at coordinates."""
        if not self._adb_device:
            return "No device"
        try:
            subprocess.run(['adb', '-s', self._adb_device, 'shell', 'input', 'tap', str(x), str(y)],
                          timeout=5)
            self._action("TAP", f"({x},{y})")
            return f"Tapped ({x},{y})"
        except Exception as e:
            return f"Tap error: {e}"
    
    def adb_input_swipe(self, x1, y1, x2, y2, duration=300):
        """Swipe gesture."""
        if not self._adb_device:
            return "No device"
        try:
            subprocess.run(['adb', '-s', self._adb_device, 'shell', 'input', 'swipe',
                           str(x1), str(y1), str(x2), str(y2), str(duration)], timeout=5)
            self._action("SWIPE", f"({x1},{y1})->({x2},{y2})")
            return f"Swiped"
        except Exception as e:
            return f"Swipe error: {e}"
    
    def adb_input_text(self, text):
        """Type text (with spaces)."""
        if not self._adb_device:
            return "No device"
        try:
            # Escape spaces and special chars
            escaped = text.replace(' ', '%s').replace('&', '\\&')
            subprocess.run(['adb', '-s', self._adb_device, 'shell', 'input', 'text', escaped],
                          timeout=5)
            self._action("TYPE", text[:30])
            return f"Typed: {text[:50]}"
        except Exception as e:
            return f"Text input error: {e}"
    
    def adb_press_key(self, keycode):
        """Press Android key (e.g., 'ENTER', 'BACK', 'HOME')."""
        keycodes = {
            'ENTER': 66, 'BACK': 4, 'HOME': 3, 'POWER': 26,
            'VOLUME_UP': 24, 'VOLUME_DOWN': 25, 'MENU': 82,
            'SEARCH': 84, 'CAMERA': 27, 'ENDCALL': 6
        }
        code = keycodes.get(keycode.upper(), keycode)
        try:
            subprocess.run(['adb', '-s', self._adb_device, 'shell', 'input', 'keyevent', str(code)],
                          timeout=5)
            self._action("KEY", keycode)
            return f"Key: {keycode}"
        except Exception as e:
            return f"Key error: {e}"
    
    def adb_start_app(self, package_name):
        """Launch Android app by package."""
        try:
            subprocess.run(['adb', '-s', self._adb_device, 'shell', 'monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'],
                          timeout=10)
            self._action("LAUNCH", package_name)
            return f"Launched {package_name}"
        except Exception as e:
            return f"Launch error: {e}"
    
    def adb_list_packages(self, filter_text=None):
        """List installed packages."""
        try:
            result = subprocess.run(['adb', '-s', self._adb_device, 'shell', 'pm', 'list', 'packages'],
                                   capture_output=True, text=True, timeout=20)
            packages = [p.replace('package:', '') for p in result.stdout.strip().split('\n')]
            if filter_text:
                packages = [p for p in packages if filter_text.lower() in p.lower()]
            return packages[:50]  # limit
        except Exception as e:
            return [f"Error: {e}"]
    
    # ==================== WEBSOCKET RELAY (Flutter App) ====================
    def relay_connect(self, host='localhost', port=8001):
        """Connect to the WebSocket relay server (Flutter mobile app)."""
        if not WEBSOCKETS_AVAILABLE:
            return "ERROR: websockets package not installed"
        
        import asyncio
        async def _connect():
            uri = f"ws://{host}:{port}/ws/jack_secure_neural_link_2026"
            try:
                self._relay_ws = await websockets.connect(uri)
                self._relay_loop = asyncio.get_event_loop()
                self._relay_connected = True
                self._emit("ACTIVE", f"Relay connected to {host}:{port}")
                return f"Connected to relay at {uri}"
            except Exception as e:
                return f"Relay connect failed: {e}"
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(_connect())
        except Exception as e:
            return f"Relay error: {e}"
    
    def relay_send_command(self, command):
        """Send command to mobile app via relay."""
        if not self._relay_connected or not self._relay_ws:
            return "Not connected to relay"
        try:
            import asyncio
            async def _send():
                await self._relay_ws.send(json.dumps({"command": command}))
            self._relay_loop.run_until_complete(_send())
            self._action("RELAY_CMD", command[:50])
            return f"Sent: {command}"
        except Exception as e:
            return f"Relay send error: {e}"
    
    def relay_broadcast_screen(self, screenshot_bytes):
        """Send screenshot to mobile app (for remote viewing)."""
        if not self._relay_connected:
            return False
        try:
            import asyncio
            b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            payload = {
                "type": "screen_update",
                "data": b64,
                "timestamp": time.time()
            }
            async def _send():
                await self._relay_ws.send(json.dumps(payload))
            self._relay_loop.run_until_complete(_send())
            return True
        except:
            return False
    
    # ==================== UNIFIED HELPERS ====================
    def get_status(self):
        return {
            'agent': 'MobileController',
            'adb_available': ADB_AVAILABLE,
            'adb_device': self._adb_device,
            'relay_connected': self._relay_connected,
            'mode': 'ADB' if self._adb_device else ('Relay' if self._relay_connected else 'OFFLINE')
        }
    
    def stop(self):
        """Cleanup."""
        try:
            if self._relay_ws:
                self._relay_ws.close()
        except: pass
        self._emit("SHUTDOWN", "MobileController stopped")
        return "MobileController stopped"


# ==================== DEMO ====================
def demo_mobile_control():
    print("\n" + "="*70)
    print("MOBILE CONTROLLER DEMO")
    print("Testing ADB + WebSocket Relay")
    print("="*70)
    
    agent = MobileController()
    
    print("\n[1] Check ADB availability...")
    if ADB_AVAILABLE:
        print("  ADB is installed")
        # Try connect
        print("\n[2] Connect to Android device...")
        res = agent.adb_connect()
        print(f"  {res}")
        if agent._adb_device:
            # Show device info
            print("\n[3] Device properties:")
            model = agent.adb_shell('getprop ro.product.model')
            print(f"  Model: {model.strip()}")
            version = agent.adb_shell('getprop ro.build.version.release')
            print(f"  Android: {version.strip()}")
            
            # Screenshot
            print("\n[4] Taking screenshot...")
            img = agent.adb_screencap()
            if img:
                img.save('mobile_screenshot.png')
                print("  Saved: mobile_screenshot.png")
            
            # Tap center (demo)
            print("\n[5] Tap center of screen...")
            print(f"  {agent.adb_input_tap(540, 960)}")
            
            # List some apps
            print("\n[6] List installed packages (filter 'chrome')...")
            pkgs = agent.adb_list_packages('chrome')
            print(f"  Found {len(pkgs)} packages")
            for p in pkgs[:5]:
                print(f"    {p}")
    else:
        print("  ADB not available - install Android SDK Platform-Tools")
    
    # WebSocket relay (requires Flutter app running)
    print("\n[7] Connect to WebSocket relay (optional)...")
    print("  (Ensure mobile app is running on same network)")
    try:
        res = agent.relay_connect(host='localhost', port=8001)
        print(f"  {res}")
    except Exception as e:
        print(f"  Relay not available: {e}")
    
    print("\n[8] Agent status:")
    st = agent.get_status()
    for k,v in st.items():
        print(f"  {k}: {v}")
    
    print("\n[9] Stopping...")
    print(agent.stop())
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    return True


if __name__ == "__main__":
    ok = demo_mobile_control()
    sys.exit(0 if ok else 1)
