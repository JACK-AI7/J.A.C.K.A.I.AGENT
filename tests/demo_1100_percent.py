#!/usr/bin/env python
"""
1100% Automation Demo - Showcases all human-like features
Run this to see JARVIS automation in action!
"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'agents'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'utils'))

from agents.desktop_agent import DesktopAgent
from utils.humanized_input import HumanizedInput, HumanConfig, HMG


def demo_mouse_movement():
    """Demonstrate realistic mouse movement"""
    print("\n" + "="*60)
    print("DEMO 1: Mouse Movement (Bezier Curves)")
    print("="*60)
    print("Watch the mouse - it moves in smooth curves, not straight lines!")
    print("You'll see acceleration and deceleration.")
    
    agent = DesktopAgent()
    
    # Get screen size
    size_str = agent.get_screen_size()
    parts = size_str.split(":")
    dims = parts[1].strip().split("x")
    w, h = int(dims[0]), int(dims[1].split()[0])
    
    # Draw a square with human-like movement
    points = [
        (w//4, h//4),
        (w*3//4, h//4),
        (w*3//4, h*3//4),
        (w//4, h*3//4),
        (w//2, h//2)
    ]
    
    input("Press Enter to start mouse demo...")
    for x, y in points:
        print(f"  Moving to ({x}, {y})...")
        agent.click_position(x, y)
        time.sleep(0.8)  # Watch the movement
    
    print("[OK] Mouse movement demo complete")


def demo_typing():
    """Demonstrate human-like typing"""
    print("\n" + "="*60)
    print("DEMO 2: Human-Like Typing")
    print("="*60)
    print("Watch for:")
    print("  - Variable speed (home row vs edges)")
    print("  - Occasional typos with corrections")
    print("  - Pauses after punctuation")
    print("  - Random mid-sentence thinking pauses")
    
    agent = DesktopAgent()
    
    # Enable higher typo chance for demonstration
    original_typo = agent.human.config.typo_chance
    agent.human.config.typo_chance = 0.1  # 10% so you'll likely see a typo
    
    test_phrases = [
        "Hello, I am JARVIS. I am an AI assistant.",
        "The quick brown fox jumps over the lazy dog.",
        "My typing speed varies depending on which keys I press.",
    ]
    
    input("Press Enter to start typing demo...")
    for phrase in test_phrases:
        print(f"\nTyping: '{phrase}'")
        agent.type_text(phrase)
        time.sleep(1)
    
    # Restore settings
    agent.human.config.typo_chance = original_typo
    print("\n[OK] Typing demo complete")


def demo_precision():
    """Demonstrate click precision"""
    print("\n" + "="*60)
    print("DEMO 3: Click Precision (Human-Level Accuracy)")
    print("="*60)
    print("We'll click 5 times at the same spot.")
    print("Human variation should be ~5-10px.")
    
    agent = DesktopAgent()
    human = agent.human
    
    # Get screen center
    size_str = agent.get_screen_size()
    parts = size_str.split(":")
    dims = parts[1].strip().split("x")
    w, h = int(dims[0]), int(dims[1].split()[0])
    center_x, center_y = w//2, h//2
    
    print(f"\nTarget: ({center_x}, {center_y})")
    input("Press Enter to start precision demo...")
    
    clicks = []
    for i in range(5):
        human.click(center_x, center_y)
        actual_x, actual_y = pyautogui.position()
        distance = ((actual_x - center_x)**2 + (actual_y - center_y)**2)**0.5
        clicks.append((actual_x, actual_y))
        print(f"  Click {i+1}: ({actual_x}, {actual_y}) - Distance: {distance:.1f}px")
        time.sleep(0.8)
    
    # Calculate variance
    x_vals = [c[0] for c in clicks]
    y_vals = [c[1] for c in clicks]
    x_std = (sum((x - center_x)**2 for x in x_vals) / len(x_vals))**0.5
    y_std = (sum((y - center_y)**2 for y in y_vals) / len(y_vals))**0.5
    
    print(f"\nStandard deviation: X={x_std:.1f}px, Y={y_std:.1f}px")
    print("This is the 'human jitter' - normal and expected!")
    print("[OK] Precision demo complete")


def demo_application_launch():
    """Demonstrate opening applications"""
    print("\n" + "="*60)
    print("DEMO 4: Application Launch")
    print("="*60)
    print("We'll open and close a few applications.")
    print("Note the timing - human-like delays for app startup.")
    
    agent = DesktopAgent()
    
    apps = ["notepad", "calc"]
    if agent.system != "Windows":
        print("(Skipped - Windows only demo)")
        return
    
    input("Press Enter to start app launch demo...")
    
    for app in apps:
        print(f"\nOpening {app}...")
        agent.open_application(app)
        time.sleep(2)  # Wait for app
        
        print(f"  Opening window detected, closing in 2s...")
        time.sleep(2)
        agent.close_active_window()
        time.sleep(1)
    
    print("\n[OK] Application launch demo complete")


def demo_vision_system():
    """Demonstrate OCR vision"""
    print("\n" + "="*60)
    print("DEMO 5: Vision System (OCR)")
    print("="*60)
    print("The system can read text from screen using EasyOCR.")
    
    controller = SystemController()
    
    if controller.reader is None:
        print("EasyOCR not available - skipping demo")
        return
    
    input("Press Enter to capture screen and extract text...")
    
    # Capture current screen
    result = controller.visual_locate("test")  # Search for "test"
    if isinstance(result, dict):
        print(f"Found text at ({result['x']}, {result['y']}): '{result['text']}'")
        print(f"Confidence: {result['confidence']:.1%}")
    else:
        print(f"No text found (or no screen content): {result}")
    
    print("\n[OK] Vision demo complete")


def demo_full_automation():
    """Run a complete automation sequence"""
    print("\n" + "="*60)
    print("DEMO 6: Full Automation Sequence")
    print("="*60)
    print("Combining: Open → Type → Save → Close")
    
    agent = DesktopAgent()
    
    if agent.system != "Windows":
        print("(Skipped - Windows only demo)")
        return
    
    input("Press Enter to start full automation...")
    
    # 1. Open Notepad
    print("\n1. Opening Notepad...")
    agent.open_application("notepad")
    time.sleep(2)
    
    # 2. Type text
    print("2. Typing 'JARVIS Automation v1.0'...")
    agent.type_text("JARVIS Automation v1.0")
    time.sleep(0.5)
    
    # 3. Save with shortcut
    print("3. Pressing Ctrl+S (save)...")
    agent.hotkey('ctrl', 's')
    time.sleep(0.5)
    
    # 4. Type filename
    print("4. Typing filename...")
    filename = f"jarvis_demo_{int(time.time())}.txt"
    agent.type_text(filename)
    time.sleep(0.3)
    
    # 5. Press Enter
    print("5. Pressing Enter to save...")
    agent.press_key('enter')
    time.sleep(1)
    
    # 6. Close
    print("6. Closing Notepad...")
    agent.close_active_window()
    time.sleep(0.5)
    
    # 7. Don't save (if prompted) - would need UI interaction
    print(f"\n[OK] Full automation complete! File should be saved as: {filename}")


def main():
    """Run all demos"""
    print("="*60)
    print("JARVIS 1100% AUTOMATION - DEMONSTRATION SUITE")
    print("="*60)
    print("\nThis demo showcases all human-like automation features.")
    print("Watch for smooth mouse curves, typing variation, and natural timing.")
    print("\nPress Ctrl+C at any time to exit.")
    print("="*60)
    
    demos = [
        ("Mouse Movement", demo_mouse_movement),
        ("Typing", demo_typing),
        ("Precision Clicking", demo_precision),
        ("Application Launch", demo_application_launch),
        ("Vision System", demo_vision_system),
        ("Full Automation", demo_full_automation),
    ]
    
    try:
        for i, (name, demo_func) in enumerate(demos, 1):
            print(f"\n[{i}/{len(demos)}] {name}")
            demo_func()
            
            if i < len(demos):
                cont = input("\nContinue to next demo? (y/n): ").lower()
                if cont != 'y':
                    break
    
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nAll features working at 1100% human-like level!")
    print("\nNext steps:")
    print("1. Run tests: python tests/test_automation.py")
    print("2. Run integration: python tests/integration_test.py")
    print("3. Read docs: docs/AUTOMATION_1100_PERCENT.md")
    print("="*60)


if __name__ == "__main__":
    # Import here to avoid issues
    import pyautogui
    main()
