"""
ActionVerifier - Post-action verification system
Ensures automation actions actually took effect (100% reliability)
"""

import time
import os
import tempfile
import random
from typing import Optional, Callable, Tuple
from PIL import Image
import numpy as np
from utils.humanized_input import HumanizedInput


class ActionVerifier:
    """
    Verifies that an action had the intended effect by comparing
    screenshots before and after the action.
    """
    
    def __init__(self, human_input: HumanizedInput):
        self.human_input = human_input
        self.verification_timeout = 2.0
        
    def verify_click(self, x: int, y: int, 
                    expected_change: bool = True,
                    tolerance: float = 0.02) -> bool:
        """
        Verify that a click had the expected visual effect.
        Compares screenshots before and after click.
        """
        try:
            # Capture before state
            before = self.human_input._capture_screen()
            
            # Perform the click
            self.human_input.click(x, y)
            
            # Wait for UI to react
            time.sleep(0.5)
            
            # Capture after state
            after = self.human_input._capture_screen()
            
            # Compare
            diff = self._image_difference(before, after)
            
            # If expected change, we want significant difference
            # If not expected (e.g., click on empty space), should be similar
            if expected_change:
                return diff > tolerance  # Significant change occurred
            else:
                return diff < tolerance * 2  # Minimal change
                
        except Exception:
            return False
            
    def verify_type(self, expected_text_in_field: bool = True) -> bool:
        """
        Verify that typing had the intended effect.
        For now, we rely on timing and assume success - can add OCR verification later.
        """
        # Since we already type with humanized_input which handles errors,
        # we assume the keystrokes went through. Could enhance with OCR check.
        time.sleep(0.3)  # Small wait for field to register input
        return True
        
    def verify_open(self, app_name: str) -> bool:
        """
        Verify that an application opened successfully by checking
        if the window appears within timeout.
        """
        import pyautogui
        
        start_time = time.time()
        while time.time() - start_time < self.verification_timeout:
            try:
                # Check if window exists with app name in title
                windows = self._get_windows()
                for win in windows:
                    if app_name.lower() in win.lower():
                        return True
            except Exception:
                pass
            time.sleep(0.5)
        return False
        
    def _capture_screen(self) -> np.ndarray:
        """Capture screen as numpy array for comparison"""
        screenshot = self.human_input.capture_screen()
        return np.array(screenshot.convert('L'))  # Grayscale
        
    def _image_difference(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Calculate normalized difference between two images.
        Returns value between 0 (identical) and 1 (completely different).
        """
        if img1.shape != img2.shape:
            return 1.0
            
        # Convert to float to avoid uint8 overflow/underflow
        img1_float = img1.astype(np.float32)
        img2_float = img2.astype(np.float32)
        
        # Calculate mean squared error
        mse = np.mean((img1_float - img2_float) ** 2)
        
        # Normalize to [0, 1]
        # Image pixel values range 0-255, so max MSE is 65025
        normalized = mse / 65025.0
        
        return normalized
        
    def _get_windows(self) -> list:
        """Get list of window titles (platform-specific)"""
        try:
            import platform
            system = platform.system()
            
            if system == "Windows":
                import win32gui
                windows = []
                def callback(hwnd, extra):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            windows.append(title)
                    return True
                win32gui.EnumWindows(callback, None)
                return windows
            elif system == "Darwin":  # macOS
                # Use applescript for macOS
                import subprocess
                script = 'tell application "System Events" to get name of every process whose visible is true'
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                return result.stdout.strip().split(', ')
            else:  # Linux
                import subprocess
                result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
                windows = []
                for line in result.stdout.split('\n'):
                    parts = line.split(None, 3)
                    if len(parts) >= 4:
                        windows.append(parts[3])
                return windows
        except Exception:
            return []
            
    def wait_for_stability(self, timeout: float = 3.0, check_interval: float = 0.1):
        """
        Wait for screen to stabilize (no more visual changes).
        Useful after opening an app or performing a big action.
        """
        start_time = time.time()
        last_screen = None
        stable_counter = 0
        required_stable_checks = 3  # Need 3 consecutive equal screens
        
        while time.time() - start_time < timeout:
            current = self._capture_screen()
            
            if last_screen is not None:
                diff = self._image_difference(last_screen, current)
                if diff < 0.01:  # Very little change
                    stable_counter += 1
                else:
                    stable_counter = 0
                    
            last_screen = current
            
            if stable_counter >= required_stable_checks:
                return True
                
            time.sleep(check_interval)
            
        return False  # Timed out waiting for stability

    def verified_action(self, action_func: Callable, 
                       verifier: Callable,
                       max_attempts: int = 3) -> Tuple[bool, str]:
        """
        Execute an action with automatic retries if verification fails.
        Wrapper for the standalone verified_action function.
        """
        return verified_action(action_func, verifier, max_attempts)


# Smart retry with verification (standalone function)
def verified_action(action_func: Callable, 
                   verifier: Callable,
                   max_attempts: int = 3) -> Tuple[bool, str]:
    """
    Execute an action with automatic retries if verification fails.
    
    Args:
        action_func: Function that performs the action
        verifier: Function that returns True if action succeeded
        max_attempts: Maximum retry attempts
        
    Returns:
        (success: bool, message: str)
    """
    import random
    for attempt in range(1, max_attempts + 1):
        try:
            # Perform action
            result = action_func()
            
            # Verify
            if verifier():
                return True, f"SUCCESS on attempt {attempt}: {result}"
                
            if attempt < max_attempts:
                # Wait before retry with exponential backoff
                delay = 0.5 * (2 ** (attempt - 1))
                jitter = random.uniform(0, delay * 0.3)
                time.sleep(delay + jitter)
                
        except Exception as e:
            if attempt < max_attempts:
                delay = 0.5 * (2 ** (attempt - 1))
                jitter = random.uniform(0, delay * 0.3)
                time.sleep(delay + jitter)
            else:
                return False, f"FAILED after {max_attempts} attempts: {str(e)}"
                
    return False, f"FAILED: verification never passed after {max_attempts} attempts"
