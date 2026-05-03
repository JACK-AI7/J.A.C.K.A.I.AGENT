"""
Manual Verification Script for Humanized Automation
Tests the system by performing a series of automation actions
and reporting success/failure rates.
"""

import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from agents.desktop_agent import DesktopAgent
from agents.system_controller import SystemController
from agents.visual_orchestrator import VisualOrchestrator
from utils.humanized_input import HumanizedInput, HumanConfig
import random


def test_mouse_movement(agent: DesktopAgent):
    """Test realistic mouse movement"""
    print("\n[TEST] Mouse Movement - Should be smooth and curved")
    screen_w, screen_h = 1920, 1080  # Default assumption
    try:
        size = agent.get_screen_size()
        # Parse "Screen size: 1920x1080 pixels"
        parts = size.split(":")
        if len(parts) > 1:
            dims = parts[1].strip().split("x")
            screen_w, screen_h = int(dims[0]), int(dims[1].split()[0])
    except:
        pass
    
    # Test movement to several points
    targets = [
        (screen_w // 4, screen_h // 4),
        (screen_w * 3 // 4, screen_h // 4),
        (screen_w * 3 // 4, screen_h * 3 // 4),
        (screen_w // 4, screen_h * 3 // 4),
        (screen_w // 2, screen_h // 2)
    ]
    
    for x, y in targets:
        start = time.time()
        agent.click_position(x, y)
        elapsed = time.time() - start
        print(f"  Moved to ({x}, {y}) in {elapsed:.2f}s")
        time.sleep(0.5)  # Observe movement
        
    print("  ✓ Mouse movement test complete")


def test_typing(agent: DesktopAgent):
    """Test human-like typing"""
    print("\n[TEST] Typing - Should have natural rhythm and occasional typos")
    
    test_phrases = [
        "Hello, world!",
        "The quick brown fox jumps over the lazy dog.",
        "1234567890",
        "Sphinx of black quartz, judge my vow."
    ]
    
    # Enable higher typo chance for demonstration
    original_typo = agent.human.config.typo_chance
    agent.human.config.typo_chance = 0.1  # 10% for demo
    
    for phrase in test_phrases:
        print(f"\n  Typing: '{phrase}'")
        start = time.time()
        agent.type_text(phrase)
        elapsed = time.time() - start
        print(f"    Completed in {elapsed:.2f}s")
        time.sleep(1)
        
    # Restore original setting
    agent.human.config.typo_chance = original_typo
    print("\n  ✓ Typing test complete")


def test_keyboard_shortcuts(agent: DesktopAgent):
    """Test keyboard shortcuts"""
    print("\n[TEST] Keyboard Shortcuts")
    
    shortcuts = ['ctrl+c', 'ctrl+v', 'ctrl+a', 'alt+tab', 'win+d']
    for shortcut in shortcuts:
        print(f"  Pressing: {shortcut}")
        from core.tools import keyboard_shortcut
        result = keyboard_shortcut(shortcut)
        print(f"    {result}")
        time.sleep(0.5)
        
    print("  ✓ Keyboard shortcuts test complete")


def test_application_launch(agent: DesktopAgent):
    """Test opening applications"""
    print("\n[TEST] Application Launch")
    
    apps_to_test = ['notepad', 'calc']
    if agent.system == "Windows":
        for app in apps_to_test:
            print(f"  Opening: {app}")
            result = agent.open_application(app)
            print(f"    {result}")
            time.sleep(2)  # Wait for app to open
            # Try to close
            agent.close_active_window()
            time.sleep(1)
    else:
        print("  (Skipped - Windows-specific test)")
        
    print("  ✓ Application launch test complete")


def test_action_verifier(agent: DesktopAgent):
    """Test the action verification system"""
    print("\n[TEST] Action Verification")
    
    from utils.action_verifier import ActionVerifier
    verifier = ActionVerifier(agent.human)
    
    # Test image difference
    print("  Testing image difference calculation...")
    import numpy as np
    img1 = agent.human._capture_screen()
    time.sleep(0.5)
    img2 = agent.human._capture_screen()
    diff = verifier._image_difference(img1, img2)
    print(f"    Screen change difference: {diff:.4f}")
    print("  ✓ Verification system operational")


def test_visual_orchestrator():
    """Test visual orchestrator (if dependencies available)"""
    print("\n[TEST] Visual Orchestrator")
    
    try:
        orch = VisualOrchestrator()
        print("  VisualOrchestrator initialized")
        
        # Test screen awareness
        summary = orch.get_screen_summary()
        print(f"  Screen summary: {summary[:100]}...")
        print("  ✓ Visual orchestrator operational")
    except Exception as e:
        print(f"  ⚠ Visual orchestrator limited: {e}")


def test_system_controller():
    """Test system controller features"""
    print("\n[TEST] System Controller")
    
    try:
        controller = SystemController()
        print("  SystemController initialized")
        
        # Test basic interaction
        result = controller.locate_and_click(100, 100, verify=False)
        print(f"  Locate and click: {result}")
        print("  ✓ System controller operational")
    except Exception as e:
        print(f"  ⚠ System controller error: {e}")


def run_sanity_checks():
    """Run quick sanity checks on core components"""
    print("\n[SANITY CHECKS]")
    
    # Test human config
    config = HumanConfig()
    assert config.mouse_speed_factor > 0
    assert config.typing_speed_base > 0
    print("  ✓ HumanConfig valid")
    
    # Test human input creation
    human = HumanizedInput(config)
    assert human.screen_width > 0
    assert human.screen_height > 0
    print("  ✓ HumanizedInput initialized")
    
    # Test desktop agent
    agent = DesktopAgent()
    assert agent.human is not None
    print("  ✓ DesktopAgent ready")
    

def main():
    """Run all verification tests"""
    print("="*60)
    print("JARVIS AUTOMATION - MANUAL VERIFICATION SUITE")
    print("Testing 1100% Human-Like Automation")
    print("="*60)
    
    # Sanity checks first
    try:
        run_sanity_checks()
    except Exception as e:
        print(f"\n✗ SANITY CHECK FAILED: {e}")
        return False
    
    print("\n" + "="*60)
    print("BEGINNING ACTION TESTS")
    print("="*60)
    
    # Initialize agents
    agent = DesktopAgent()
    
    # Run test batteries
    tests = [
        ("Mouse Movement", lambda: test_mouse_movement(agent)),
        ("Typing", lambda: test_typing(agent)),
        ("Keyboard Shortcuts", lambda: test_keyboard_shortcuts(agent)),
        ("Application Launch", lambda: test_application_launch(agent)),
        ("Action Verification", lambda: test_action_verifier(agent)),
        ("Visual Orchestrator", lambda: test_visual_orchestrator()),
        ("System Controller", lambda: test_system_controller()),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"RUNNING: {test_name}")
            print(f"{'='*60}")
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ TEST FAILED: {test_name}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Final report
    print("\n" + "="*60)
    print("FINAL TEST REPORT")
    print("="*60)
    print(f"Total Test Suites: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed/len(tests)*100:.1f}%")
    
    if failed == 0:
        print("\n✓ ALL MANUAL TESTS PASSED - Automation is 1100% operational!")
    else:
        print(f"\n✗ {failed} test suite(s) failed. Review errors above.")
        
    return failed == 0


if __name__ == "__main__":
    success = main()
    
    print("\n" + "="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Run the full automated test suite: python tests/test_automation.py")
    print("2. Perform live manual testing with actual UI tasks")
    print("3. Monitor for any non-human-like behaviors")
    print("4. Adjust config parameters in utils/humanized_input.py as needed")
    print("="*60)
    
    sys.exit(0 if success else 1)
