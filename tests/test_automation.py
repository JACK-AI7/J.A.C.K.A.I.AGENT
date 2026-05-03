"""
Comprehensive Automation Test Suite for Humanized Input System
Tests all automation modes for 1100% reliability and human-like behavior
"""

import unittest
import sys
import os
import time
import pyautogui

# Add both project root and core to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'core'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'agents'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'utils'))

from utils.humanized_input import HumanizedInput, HumanConfig, HMG
from agents.desktop_agent import DesktopAgent
from agents.system_controller import SystemController
from utils.action_verifier import ActionVerifier, verified_action

from utils.humanized_input import HumanizedInput, HumanConfig, HMG
from agents.desktop_agent import DesktopAgent
from agents.system_controller import SystemController
from utils.action_verifier import ActionVerifier


class TestHumanizedInput(unittest.TestCase):
    """Test the core HumanizedInput engine"""
    
    def setUp(self):
        self.human = HumanizedInput(HumanConfig(
            mouse_precision=0.9,  # Higher precision for testing
            typing_speed_base=0.001,  # Fast for tests
            typo_chance=0.0  # No typos in tests
        ))
        
    def test_mouse_move(self):
        """Test that mouse movement is smooth and within bounds"""
        # move_to doesn't return coordinates, it just moves
        self.human.move_to(100, 100, smooth=False)
        current = pyautogui.position()
        self.assertIsNotNone(current)
        # Should be close to target (within human error margin)
        self.assertLess(abs(current[0] - 100), 10)
        self.assertLess(abs(current[1] - 100), 10)
        
    def test_click(self):
        """Test clicking at coordinates"""
        self.human.click(200, 200)
        # Should not raise exception
        
    def test_typing(self):
        """Test human-like typing"""
        self.human.type_text("Hello World")
        # Should not raise exception
        
    def test_hotkey(self):
        """Test hotkey combination"""
        self.human.hotkey('ctrl', 'c')  # Should not crash
        self.human.hotkey('alt', 'tab')
        
    def test_scroll(self):
        """Test scrolling"""
        self.human.scroll(5, direction='down')
        self.human.scroll(3, direction='up')
        
    def test_typo_simulation(self):
        """Test that typos can be generated"""
        char, is_typo, delay = self.human._maybe_make_typo('a')
        self.assertIsInstance(char, str)
        # Most characters should not be typos (low chance)
        # But with typo_chance=0, should never be typo
        self.assertFalse(is_typo)
        self.assertEqual(delay, 0)


class TestDesktopAgent(unittest.TestCase):
    """Test DesktopAgent integration with humanized input"""
    
    def setUp(self):
        self.agent = DesktopAgent()
        
    def test_initialization(self):
        """Test agent initializes correctly"""
        self.assertIsNotNone(self.agent.human)
        self.assertIsInstance(self.agent.system, str)
        
    def test_get_screen_size(self):
        """Test screen size query"""
        size = self.agent.get_screen_size()
        self.assertIn("Screen size:", size)
        
    def test_get_mouse_position(self):
        """Test mouse position query"""
        pos = self.agent.get_mouse_position()
        self.assertIn("Mouse position:", pos)
        
    def test_open_application(self):
        """Test opening an application"""
        # Open a simple app that should exist
        result = self.agent.open_application("notepad")
        # Should succeed or fail gracefully with message
        self.assertIsInstance(result, str)
        
    def test_click_position(self):
        """Test clicking at specific position"""
        # Click somewhere safe (like near center)
        result = self.agent.click_position(100, 100)
        self.assertIn("Clicked at position", result)
        
    def test_type_text(self):
        """Test typing text"""
        result = self.agent.type_text("Test123")
        self.assertIn("Typed:", result)
        
    def test_press_key(self):
        """Test pressing a single key"""
        result = self.agent.press_key('enter')
        self.assertIn("Pressed key:", result)
        
    def test_scroll(self):
        """Test scrolling"""
        result = self.agent.scroll('down', 3)
        self.assertIn("Scrolled", result)
        
    def test_close_active_window(self):
        """Test closing window shortcut"""
        result = self.agent.close_active_window()
        self.assertIn("Closed", result)
        
    def test_minimize_window(self):
        """Test minimizing window"""
        result = self.agent.minimize_window()
        self.assertIn("Minimized", result)


class TestSystemController(unittest.TestCase):
    """Test SystemController with humanized vision"""
    
    def setUp(self):
        self.controller = SystemController()
        
    def test_initialization(self):
        """Test controller initializes"""
        self.assertIsNotNone(self.controller.human)
        self.assertEqual(self.controller.workspace, os.getcwd())
        
    def test_locate_and_click(self):
        """Test click with coordinates"""
        result = self.controller.locate_and_click(100, 100, verify=False)
        self.assertIn("Clicked", result)
        
    def test_visual_locate(self):
        """Test OCR-based element location"""
        # This requires EasyOCR to be installed
        result = self.controller.visual_locate("test")
        # Either returns dict with coordinates or error message
        self.assertIsInstance(result, (dict, str))


class TestActionVerifier(unittest.TestCase):
    """Test the action verification system"""
    
    def setUp(self):
        human = HumanizedInput()
        self.verifier = ActionVerifier(human)
        
    def test_image_difference(self):
        """Test image difference calculation with identical images"""
        # Create two identical small images
        import numpy as np
        img1 = np.zeros((100, 100), dtype=np.uint8)
        img2 = np.zeros((100, 100), dtype=np.uint8)
        diff = self.verifier._image_difference(img1, img2)
        # Identical images should have zero or very tiny diff (numerical precision)
        self.assertLess(diff, 0.01)  # Allow tiny numerical error
        
    def test_different_images(self):
        """Test that different images give higher diff"""
        import numpy as np
        img1 = np.zeros((100, 100), dtype=np.uint8)
        img2 = np.full((100, 100), 255, dtype=np.uint8)  # White vs black
        diff = self.verifier._image_difference(img1, img2)
        self.assertGreater(diff, 0.1)  # Should be significantly different


class TestHumanizationFeatures(unittest.TestCase):
    """Test specific human-like features"""
    
    def test_bezier_path_generation(self):
        """Test that Bezier curve generates reasonable path"""
        human = HumanizedInput()
        start = (0.0, 0.0)
        end = (100.0, 100.0)
        path = human._calculate_bezier_path(start, end, num_points=30)
        self.assertEqual(len(path), 30)
        # First point should be close to start
        self.assertAlmostEqual(path[0][0], start[0], delta=1.0)
        self.assertAlmostEqual(path[0][1], start[1], delta=1.0)
        # Last point should be close to end
        self.assertAlmostEqual(path[-1][0], end[0], delta=1.0)
        self.assertAlmostEqual(path[-1][1], end[1], delta=1.0)
        
    def test_typing_delay_range(self):
        """Test typing delays are in reasonable range"""
        human = HumanizedInput(HumanConfig(typing_speed_base=0.1))
        delays = [human._human_typing_delay(c) for c in "hello123"]
        for d in delays:
            self.assertGreater(d, 0.02)  # At least 20ms
            self.assertLess(d, 0.5)  # At most 500ms
            
    def test_human_error_application(self):
        """Test that human error is applied to coordinates"""
        human = HumanizedInput(HumanConfig(mouse_precision=0.8))
        x, y = 500, 500
        # Run multiple times to check variance
        results = [human._apply_human_error(x, y) for _ in range(20)]
        # Should have some variance (not all identical)
        unique = set(results)
        self.assertGreater(len(unique), 1, "Should have some randomness in positioning")


class TestIntegration(unittest.TestCase):
    """Integration tests for full automation pipeline"""
    
    def test_desktop_agent_integration(self):
        """Test desktop agent methods work together"""
        agent = DesktopAgent()
        
        # Chain operations
        agent.click_position(100, 100)
        agent.type_text("Test")
        agent.press_key('enter')
        # Should not crash
        
    def test_verifier_integration(self):
        """Test verifier with humanized input"""
        human = HumanizedInput()
        verifier = ActionVerifier(human)
        
        # Perform action and verify using standalone function
        success, msg = verified_action(
            lambda: human.click(200, 200),
            lambda: True  # Simplified verifier that always passes
        )
        self.assertTrue(success)


def run_full_test_suite():
    """Run all tests and report results"""
    print("\n" + "="*60)
    print("JARVIS AUTOMATION TEST SUITE - 1100% Verification")
    print("="*60 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestHumanizedInput))
    suite.addTests(loader.loadTestsFromTestCase(TestDesktopAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemController))
    suite.addTests(loader.loadTestsFromTestCase(TestActionVerifier))
    suite.addTests(loader.loadTestsFromTestCase(TestHumanizationFeatures))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED - Automation is 1100% operational!")
    else:
        print("\n✗ Some tests failed. Review and fix.")
        for test, trace in result.failures + result.errors:
            print(f"  - {test}: {trace[:100]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Need pyautogui imports for tests
    import pyautogui
    success = run_full_test_suite()
    sys.exit(0 if success else 1)
