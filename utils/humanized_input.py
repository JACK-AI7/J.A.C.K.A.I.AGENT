"""
HumanizedInput - Ultra-Realistic Desktop Automation Engine
Makes automation indistinguishable from human behavior (1100% realism)
"""

import time
import random
import math
import numpy as np
import pyautogui
from typing import Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from PIL import Image


class HMG (Enum):
    """Human Movement Genetics - different user profiles"""
    PRECISE = 0.95     # Very steady hand (high accuracy, slower)
    NORMAL  = 1.0      # Average human
    TREMOR  = 1.1      # Slight hand tremor
    FATIGUED = 1.2     # Slower, less accurate


@dataclass
class HumanConfig:
    """Configuration for human-like behavior"""
    # Mouse settings
    mouse_speed_factor: float = 1.0          # Overall speed multiplier
    mouse_precision: float = 0.85            # Accuracy (1.0 = pixel perfect, lower = more error)
    movement_profile: HMG = HMG.NORMAL       # Movement genetics profile
    
    # Typing settings  
    typing_speed_base: float = 0.08          # Base delay per key (seconds)
    typing_variance: float = 0.05            # Random variance in typing speed
    typo_chance: float = 0.015              # Chance of making a typo per character (~1.5%)
    correction_delay: float = 0.3            # Time to realize and fix typo
    
    # Natural behavior settings
    think_time_min: float = 0.2             # Minimum pause between actions
    think_time_max: float = 1.5             # Maximum pause between actions
    micro_movement_jitter: float = 0.5      # Amount of tiny random movements
    
    # Retry settings
    max_action_retries: int = 3             # How many times to retry failed action
    retry_backoff_base: float = 0.5         # Base delay for exponential backoff
    
    # Verification
    enable_verification: bool = True        # Take screenshot after action to verify
    verification_timeout: float = 2.0       # Wait time before verification


class HumanizedInput:
    """Ultra-realistic desktop automation system that mimics human behavior"""
    
    def __init__(self, config: Optional[HumanConfig] = None):
        self.config = config or HumanConfig()
        
        # State tracking for realism
        self.last_action_time = 0
        self.current_target = None
        self.action_history = []
        
        # Ensure pyautogui is configured safely
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.01  # Minimal pause, we control timing
        
        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Initialize random seed based on time for variety
        random.seed(time.time())
        
    def _natural_delay(self, reason: str = "thinking"):
        """Add a human-like thinking pause"""
        delay = random.uniform(
            self.config.think_time_min, 
            self.config.think_time_max
        )
        # Scale by movement profile
        delay *= self.config.movement_profile.value
        time.sleep(delay)
        
    def _calculate_bezier_path(self, start: Tuple[float, float], 
                               end: Tuple[float, float], 
                               num_points: int = 30) -> np.ndarray:
        """
        Calculate a smooth Bezier curve path from start to end.
        Humans don't move in straight lines - there's always curvature.
        """
        # Generate 1-2 random control points for natural curvature
        # More control points = more complex, human-like path
        
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        
        # Add randomness to control point based on distance
        distance = math.sqrt((end[0]-start[0])**2 + (end[1]-start[1])**2)
        offset_factor = min(distance * 0.2, 100)  # Max offset based on distance
        
        # Control point offset (perpendicular to direct line)
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        
        # Perpendicular direction
        if abs(dx) > 0.001 or abs(dy) > 0.001:
            perp_x = -dy / (math.sqrt(dx*dx + dy*dy) + 1e-10)
            perp_y = dx / (math.sqrt(dx*dx + dy*dy) + 1e-10)
        else:
            perp_x, perp_y = 1, 0
            
        # Random direction (left or right of path)
        direction = random.choice([-1, 1])
        offset_magnitude = random.uniform(0.3, 1.0) * offset_factor
        
        control_x = mid_x + perp_x * offset_magnitude * direction
        control_y = mid_y + perp_y * offset_magnitude * direction
        
        # Quadratic Bezier curve: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
        path = []
        for i in range(num_points):
            t = i / (num_points - 1)
            x = (1-t)**2 * start[0] + 2*(1-t)*t * control_x + t**2 * end[0]
            y = (1-t)**2 * start[1] + 2*(1-t)*t * control_y + t**2 * end[1]
            path.append((x, y))
            
        return np.array(path)
    
    def _human_mouse_speed(self, distance: float, point_count: int) -> float:
        """
        Calculate human-like per-step delay considering:
        - Acceleration from stop
        - Deceleration before arrival
        - Variable speed during movement
        """
        # Base delay (seconds per step)
        base_delay = 0.008  # ~125 FPS for smooth movement
        
        # Adjust by speed factor
        base_delay *= (2.0 - self.config.mouse_speed_factor)
        
        # S-curve acceleration profile (0 to 1 over first 20% of path)
        # and deceleration (1 to 0 over last 20% of path)
        
        # Build speed profile
        speeds = []
        for i in range(point_count):
            t = i / (point_count - 1) if point_count > 1 else 0
            
            # S-curve: smooth 0->1->0 transition
            if t < 0.2:
                # Acceleration phase
                speed = math.sin(t * math.pi / 0.4)  # 0 to 1
            elif t > 0.8:
                # Deceleration phase
                speed = math.sin((1-t) * math.pi / 0.4)  # 1 to 0
            else:
                speed = 1.0
                
            # Add natural variation
            speed *= random.uniform(0.9, 1.1)
            speeds.append(speed)
            
        # Adjust delays inversely to speed
        delays = [base_delay / max(s, 0.1) for s in speeds]
        
        return delays
    
    def move_to(self, x: int, y: int, smooth: bool = True):
        """
        Move mouse to coordinates (x, y) with realistic human movement.
        
        Args:
            x, y: Target screen coordinates
            smooth: If True, use Bezier curve with variable speed (most human-like)
                   If False, move quickly (less natural but faster)
        """
        current_x, current_y = pyautogui.position()
        
        if not smooth or self.config.movement_profile == HMG.PRECISE:
            # Quick, straight movement (still with tiny jitter)
            duration = self._estimate_movement_time(current_x, current_y, x, y)
            pyautogui.moveTo(x, y, duration=duration, 
                           tween=pyautogui.easeInOutQuad)
        else:
            # Smooth Bezier curve movement
            target_x, target_y = self._apply_human_error(x, y)
            
            # Generate path
            path = self._calculate_bezier_path(
                (current_x, current_y), 
                (target_x, target_y),
                num_points=random.randint(25, 40)
            )
            
            # Calculate per-step delays for realistic speed profile
            delays = self._human_mouse_speed(0, len(path))
            
            # Execute movement
            for i, (px, py) in enumerate(path):
                # Add micro-jitter (tiny tremor)
                jitter_x = random.uniform(-self.config.micro_movement_jitter, 
                                          self.config.micro_movement_jitter)
                jitter_y = random.uniform(-self.config.micro_movement_jitter, 
                                          self.config.micro_movement_jitter)
                
                pyautogui.moveTo(px + jitter_x, py + jitter_y, 
                               duration=delays[i] if i < len(delays) else 0.001)
                
                # Small pause for screen refresh
                if delays[i] > 0.005:
                    time.sleep(delays[i] * 0.5)  # Use half the calculated delay
                    
            # Final precise adjustment to target (human hand refinement)
            final_x, final_y = self._apply_human_error(x, y, precise=True)
            pyautogui.moveTo(final_x, final_y, duration=0.05)
            
        self.last_action_time = time.time()
        
    def _estimate_movement_time(self, x1, y1, x2, y2) -> float:
        """Estimate time for mouse movement based on distance"""
        distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)
        # Human mouse speed: ~800-1000 pixels per second
        base_speed = 900  # pixels/second
        speed = base_speed * self.config.mouse_speed_factor
        return distance / speed
    
    def _apply_human_error(self, x: int, y: int, precise: bool = False) -> Tuple[int, int]:
        """
        Apply human-like error to coordinates.
        Humans can't click precisely - there's always slight variation.
        """
        if precise:
            # Final click - very small error
            error = self.config.mouse_precision * random.uniform(0, 1.5)
        else:
            # Normal positioning - more error
            error = self.config.mouse_precision * random.uniform(0, 3.0)
            
        # Error tends to be larger when tired/hand tremors
        error *= self.config.movement_profile.value
        
        new_x = int(x + random.uniform(-error, error))
        new_y = int(y + random.uniform(-error, error))
        
        # Clamp to screen bounds
        new_x = max(0, min(self.screen_width - 1, new_x))
        new_y = max(0, min(self.screen_height - 1, new_y))
        
        return new_x, new_y
    
    def click(self, x: Optional[int] = None, y: Optional[int] = None, 
              button: str = 'left', clicks: int = 1):
        """
        Perform a human-like click.
        If x,y are None, clicks at current position.
        """
        if x is not None and y is not None:
            self.move_to(x, y)
            
        # Human reaction time before clicking
        self._natural_delay("aiming")
        
        # Human hand tremble before click - slight movement
        current_x, current_y = pyautogui.position()
        tremor_x = random.uniform(-2, 2)
        tremor_y = random.uniform(-2, 2)
        pyautogui.moveTo(current_x + tremor_x, current_y + tremor_y, duration=0.05)
        
        # Actual click with realistic timing
        pyautogui.click(button=button, clicks=clicks, 
                       interval=random.uniform(0.1, 0.3))
        
        # Human hand settles after click
        time.sleep(random.uniform(0.05, 0.15))
        
        self.last_action_time = time.time()
        
    def double_click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Human double-click (not too fast, not too slow)"""
        self.click(x, y)
        # Human double-click interval: 200-400ms
        time.sleep(random.uniform(0.2, 0.4))
        self.click(None, None)
        
    def right_click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Right mouse button click"""
        if x is not None and y is not None:
            self.move_to(x, y)
        self._natural_delay("contextualizing")
        pyautogui.click(button='right')
        self.last_action_time = time.time()
        
    def _human_typing_delay(self, char: str) -> float:
        """
        Calculate human-like delay for a specific character.
        Different characters take different times to type.
        """
        base = self.config.typing_speed_base
        
        # Character-specific delays
        char_lower = char.lower()
        
        if char in ' ,.:;':
            # Whitespace and punctuation - frequent, fast
            char_delay = base * random.uniform(0.7, 1.0)
        elif char in '-/\\':
            # Symbol keys - need shift or careful location
            char_delay = base * random.uniform(1.2, 1.8)
        elif char in '+=[]{}':
            # Shift+key combinations
            char_delay = base * random.uniform(1.3, 2.0)
        elif char in '0123456789':
            # Number row - relatively fast
            char_delay = base * random.uniform(0.9, 1.3)
        elif char in 'abcdefghijklmnopqrstuvwxyz':
            # Letter keys - home row vs edge affects speed
            home_row = 'asdfghjkl'
            if char_lower in home_row:
                char_delay = base * random.uniform(0.8, 1.1)  # Fast (home row)
            else:
                char_delay = base * random.uniform(1.0, 1.4)  # Slower (edges)
        else:
            # Unknown char (uppercase, special)
            char_delay = base * random.uniform(1.2, 1.8)
            
        # Add variance
        char_delay *= random.uniform(1.0 - self.config.typing_variance,
                                     1.0 + self.config.typing_variance)
        
        # Apply movement profile
        char_delay *= self.config.movement_profile.value
        
        return max(0.02, char_delay)  # Minimum 20ms between keys
    
    def _maybe_make_typo(self, char: str) -> Tuple[str, bool, float]:
        """
        Occasionally make a typo and need to correct it.
        Returns: (char_to_type, is_typo, correction_delay_if_typo)
        """
        if random.random() < self.config.typo_chance:
            # Common typo patterns
            typo_patterns = {
                'a': 's', 's': 'a', 'd': 'f', 'f': 'd',  # Adjacent home row
                'j': 'k', 'k': 'j', 'l': 'k',  # Right home row
                'q': 'w', 'w': 'q', 'e': 'w', 'r': 'e',  # Top row left
                't': 'r', 'y': 't', 'u': 'y', 'i': 'u', 'o': 'i', 'p': 'o',  # Top row right
                'z': 'x', 'x': 'z', 'c': 'x', 'v': 'c', 'b': 'v', 'n': 'b', 'm': 'n',  # Bottom row
                '1': '2', '2': '3', '3': '4', '4': '5',  # Number row
                '5': '6', '6': '7', '7': '8', '8': '9', '9': '0',
            }
            
            # Sometimes double-letter error (press key twice)
            if random.random() < 0.3:
                # Double the character (e.g., "heloo")
                return char, False, 0  # Will be handled by type_text logic
            
            # Single adjacent key typo
            typo_char = typo_patterns.get(char.lower(), char)
            if typo_char != char:
                # Return lowercase typo
                return typo_char if char.islower() else typo_char.upper(), True, self.config.correction_delay
                
        return char, False, 0
    
    def type_text(self, text: str, interval: Optional[float] = None):
        """
        Type text with human-like characteristics:
        - Variable speed per character
        - Occasional typos with corrections
        - Natural pauses between words
        - Random思考で pauses
        """
        if interval is not None:
            # Override with constant interval if explicitly provided
            pyautogui.write(text, interval=interval)
            return
            
        i = 0
        while i < len(text):
            char = text[i]
            
            # Check if we should make a typo here
            typo_char, is_typo, correction_delay = self._maybe_make_typo(char)
            
            # Type the character (or typo)
            delay = self._human_typing_delay(typo_char if is_typo else char)
            time.sleep(delay)
            
            pyautogui.write(typo_char if is_typo else char)
            
            if is_typo:
                # Human realizes mistake after a short delay
                time.sleep(correction_delay + random.uniform(0.1, 0.3))
                
                # Backspace to delete typo
                time.sleep(self._human_typing_delay('backspace'))
                pyautogui.press('backspace')
                
                # Small pause before retyping
                time.sleep(random.uniform(0.1, 0.2))
                
                # Type the correct character
                delay = self._human_typing_delay(char)
                time.sleep(delay)
                pyautogui.write(char)
            else:
                # Check for word-end pause (space or punctuation)
                if char in ' .,!?;:\n':
                    # Longer pause after punctuation/space
                    word_end_pause = random.uniform(0.15, 0.4)
                    time.sleep(word_end_pause)
                elif char in '-–':
                    # Dash - thinking pause
                    time.sleep(random.uniform(0.2, 0.5))
                    
            # Occasionally glance away (longer random pause)
            if random.random() < 0.02:  # 2% chance per character
                self._natural_delay("thinking")
                
            i += 1
            
            # Occasionally pause mid-word (human thinking)
            if i < len(text) and char not in ' .,!?;:\n':
                if random.random() < 0.01:  # 1% chance
                    time.sleep(random.uniform(0.3, 0.8))
                    
        self.last_action_time = time.time()
        
    def press_key(self, key: str, presses: int = 1):
        """Press a key with human-like timing"""
        for _ in range(presses):
            delay = self._human_typing_delay(key)
            time.sleep(delay)
            pyautogui.press(key)
            if presses > 1:
                time.sleep(random.uniform(0.05, 0.15))
        self.last_action_time = time.time()
        
    def hotkey(self, *keys):
        """Press a hotkey combination with realistic timing"""
        # Human presses modifier keys first, then main key
        modifiers = keys[:-1]
        main_key = keys[-1]
        
        # Press modifiers
        for mod in modifiers:
            pyautogui.keyDown(mod)
            time.sleep(random.uniform(0.05, 0.15))
            
        # Press and release main key
        time.sleep(random.uniform(0.08, 0.2))
        pyautogui.press(main_key)
        
        # Release modifiers in reverse order (natural)
        time.sleep(random.uniform(0.05, 0.15))
        for mod in reversed(modifiers):
            pyautogui.keyUp(mod)
            
        self.last_action_time = time.time()
        
    def drag_to(self, x: int, y: int, button: str = 'left', duration: Optional[float] = None):
        """Drag from current position to target with human-like movement"""
        if duration is None:
            distance = math.sqrt((x - pyautogui.position()[0])**2 + 
                                (y - pyautogui.position()[1])**2)
            duration = distance / 500  # ~500 px/sec drag speed
            
        # Human drag is slower and less precise
        duration *= random.uniform(1.1, 1.4)
        
        pyautogui.mouseDown(button=button)
        
        # Curved drag path
        path = self._calculate_bezier_path(
            pyautogui.position(), (x, y), num_points=random.randint(15, 25)
        )
        delays = self._human_mouse_speed(0, len(path))
        
        for i, (px, py) in enumerate(path):
            pyautogui.moveTo(px, py, duration=delays[i] if i < len(delays) else 0.005)
            if delays[i] > 0.005:
                time.sleep(delays[i] * 0.5)
                
        time.sleep(random.uniform(0.1, 0.3))  # Pause before releasing
        pyautogui.mouseUp(button=button)
        self.last_action_time = time.time()
        
    def scroll(self, clicks: int = 1, direction: str = 'down', 
               x: Optional[int] = None, y: Optional[int] = None):
        """Scroll with human-like variable speed"""
        if x is not None and y is not None:
            self.move_to(x, y, smooth=True)
            
        # Human scroll is not perfectly consistent
        for _ in range(abs(clicks)):
            # Randomize scroll amount slightly
            actual_clicks = int(clicks * random.uniform(0.8, 1.2))
            pyautogui.scroll(actual_clicks if direction == 'up' else -actual_clicks)
            time.sleep(random.uniform(0.05, 0.2))
            
        self.last_action_time = time.time()
        
    def capture_screen(self) -> Image.Image:
        """Capture screen as PIL Image"""
        return pyautogui.screenshot()
        
    def capture_screen_to_file(self, filepath: str):
        """Save screenshot to file"""
        pyautogui.screenshot(filepath)
        
    def _capture_screen(self) -> np.ndarray:
        """Capture screen as numpy array for comparison"""
        screenshot = pyautogui.screenshot()
        return np.array(screenshot.convert('L'))  # Grayscale


# Retry decorator for robust automation
def with_retry(max_attempts: int = 3, 
               base_delay: float = 0.5,
               verify_func: Optional[Callable] = None):
    """
    Decorator for actions that should be retried on failure.
    Includes exponential backoff with jitter.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            human_input: HumanizedInput = kwargs.get('human_input', None)
            
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # If verification function provided, check success
                    if verify_func and not verify_func(result):
                        if attempt < max_attempts:
                            delay = base_delay * (2 ** (attempt - 1))  # Exponential
                            jitter = random.uniform(0, delay * 0.3)
                            time.sleep(delay + jitter)
                            continue
                        else:
                            return f"FAILED after {max_attempts} attempts: {result}"
                            
                    return result
                    
                except Exception as e:
                    if attempt < max_attempts:
                        delay = base_delay * (2 ** (attempt - 1))
                        jitter = random.uniform(0, delay * 0.3)
                        time.sleep(delay + jitter)
                    else:
                        return f"ERROR after {max_attempts} attempts: {str(e)}"
                        
            return "UNKNOWN_ERROR"
        return wrapper
    return decorator


# Global instance for convenience
human_input = HumanizedInput()
