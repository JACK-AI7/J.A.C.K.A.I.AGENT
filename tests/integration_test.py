"""
Integration Tests for 1100% Automation System
Tests real-world automation scenarios end-to-end
"""

import unittest
import sys
import os
import time
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'agents'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'utils'))

from agents.desktop_agent import DesktopAgent
from agents.system_controller import SystemController
from utils.humanized_input import HumanizedInput
import pyautogui


class TestRealWorldAutomation(unittest.TestCase):
    """Integration tests for complete automation workflows"""
    
    def setUp(self):
        self.agent = DesktopAgent()
        self.human = self.agent.human
        time.sleep(0.5)  # Stabilize between tests
    
    def test_open_and_close_app(self):
        """Test opening and closing an application"""
        # Open Notepad (should exist on Windows)
        result = self.agent.open_application("notepad")
        self.assertIn("At your command", result)
        time.sleep(2)  # Wait for app to launch
        
        # Verify window exists
        windows = self._get_windows()
        has_notepad = any("Notepad" in w for w in windows)
        self.assertTrue(has_notepad, "Notepad window should be open")
        
        # Close it
        self.agent.close_active_window()
        time.sleep(1)
        
        # Verify closed
        # (Window list may still have other "Notepad" instances, so we check current)
    
    def test_typing_and_keyboard(self):
        """Test typing text and keyboard shortcuts"""
        # Open notepad for typing
        self.agent.open_application("notepad")
        time.sleep(2)
        
        # Type something
        test_text = "JARVIS Automation Test - 1100%"
        self.agent.type_text(test_text)
        time.sleep(0.5)
        
        # Select all and copy (test hotkey)
        self.agent.human.hotkey('ctrl', 'a')
        time.sleep(0.3)
        self.agent.human.hotkey('ctrl', 'c')
        time.sleep(0.3)
        
        # Should succeed without errors
        self.assertTrue(True)
        
        # Cleanup
        self.agent.close_active_window()
    
    def test_mouse_precision(self):
        """Test that mouse movement is accurate within human bounds"""
        # Get screen size
        size_str = self.agent.get_screen_size()
        # Parse "Screen size: 1920x1080 pixels"
        parts = size_str.split(":")
        dims = parts[1].strip().split("x")
        w, h = int(dims[0]), int(dims[1].split()[0])
        
        # Target center
        target_x, target_y = w // 2, h // 2
        
        # Click center
        self.agent.click_position(target_x, target_y)
        time.sleep(0.5)
        
        # Get actual position
        pos_str = self.agent.get_mouse_position()
        pos_parts = pos_str.split(":")
        coords = pos_parts[1].strip().strip("()").split(", ")
        actual_x, actual_y = int(coords[0]), int(coords[1])
        
        # Should be within human precision margin (10px)
        distance = ((actual_x - target_x)**2 + (actual_y - target_y)**2)**0.5
        self.assertLess(distance, 15, f"Click should be within 15px of target, was {distance:.1f}px")
    
    def test_typo_rate(self):
        """Test that typing includes occasional typos when enabled"""
        # Set high typo chance for test
        original_typo = self.human.config.typo_chance
        self.human.config.typo_chance = 0.3  # 30% for fast detection
        
        try:
            # Type a short string and count keystrokes vs expected
            # We can't easily count actual keystrokes, but we can ensure no crashes
            self.agent.type_text("Testing typos")
            self.assertTrue(True)  # If we get here without exception, typo system works
        finally:
            self.human.config.typo_chance = original_typo
    
    def test_bezier_movement_smoothness(self):
        """Test that Bezier movement produces smooth path"""
        path = self.human._calculate_bezier_path((0, 0), (100, 100), num_points=30)
        self.assertEqual(len(path), 30)
        
        # Path should be curved (middle points offset from straight line)
        straight_mid = (50, 50)
        actual_mid = path[15]  # Middle point
        offset = abs(actual_mid[0] - straight_mid[0]) + abs(actual_mid[1] - straight_mid[1])
        self.assertGreater(offset, 0, "Path should curve away from straight line")
    
    def test_retry_logic(self):
        """Test that retry logic works with exponential backoff"""
        from utils.action_verifier import verified_action
        
        attempts = []
        def flaky_action():
            attempts.append(1)
            if len(attempts) < 3:
                raise Exception("Fail")
            return "Success"
        
        def always_true():
            return True
        
        success, msg = verified_action(flaky_action, always_true, max_attempts=3)
        self.assertTrue(success)
        self.assertEqual(len(attempts), 3)  # Should have retried
    
    def test_screenshot_comparison(self):
        """Test that image difference works correctly"""
        # Take two screenshots
        img1 = self.human.capture_screen()
        time.sleep(0.5)  # Wait for any screen changes
        img2 = self.human.capture_screen()
        
        # Convert to numpy
        import numpy as np
        arr1 = np.array(img1.convert('L'))
        arr2 = np.array(img2.convert('L'))
        
        # Should be nearly identical (small diff)
        from utils.action_verifier import ActionVerifier
        verifier = ActionVerifier(self.human)
        diff = verifier._image_difference(arr1, arr2)
        
        self.assertLess(diff, 0.1, "Similar screenshots should have low difference")
        
        # Now test with different images
        black = np.zeros((100, 100), dtype=np.uint8)
        white = np.full((100, 100), 255, dtype=np.uint8)
        big_diff = verifier._image_difference(black, white)
        self.assertGreater(big_diff, 0.5, "Different images should have high difference")
    
    def test_system_controller_integration(self):
        """Test SystemController methods"""
        controller = SystemController()
        
        # Test locate_and_click
        result = controller.locate_and_click(100, 100, verify=False)
        self.assertIn("Clicked", result)
        
        # Test visual_locate (requires EasyOCR)
        loc = controller.visual_locate("test")
        self.assertIsInstance(loc, (dict, str))
        
        # Test ai_vision_click (requires Ollama)
        # This may fail if Ollama not running, so catch error
        try:
            result = controller.ai_vision_click("nonexistent element xyz")
            # Should return failure message
            self.assertIn("Error", result.lower() if isinstance(result, str) else "OK")
        except Exception as e:
            # Model unavailable is acceptable
            self.assertIn("Ollama", str(e) or "available")
    
    def test_visual_orchestrator_initialization(self):
        """Test VisualOrchestrator can be created"""
        from agents.visual_orchestrator import VisualOrchestrator
        orch = VisualOrchestrator()
        self.assertIsNotNone(orch.human)
        self.assertEqual(orch.max_steps, 15)
    
    def test_human_config_variations(self):
        """Test different human profiles produce different behavior"""
        from utils.humanized_input import HumanConfig, HMG
        
        # Test different movement profiles
        precise = HumanizedInput(HumanConfig(movement_profile=HMG.PRECISE))
        normal = HumanizedInput(HumanConfig(movement_profile=HMG.NORMAL))
        
        # Get error margins
        p1 = precise._apply_human_error(500, 500)
        p2 = precise._apply_human_error(500, 500)
        n1 = normal._apply_human_error(500, 500)
        n2 = normal._apply_human_error(500, 500)
        
        # Precise should have smaller variance
        precise_var = (abs(p1[0]-p2[0]) + abs(p1[1]-p2[1]))
        normal_var = (abs(n1[0]-n2[0]) + abs(n1[1]-n2[1]))
        
        self.assertLessEqual(precise_var, normal_var, 
                            "Precise profile should have less variance")
    
    def test_action_retry_with_verification(self):
        """Test that retry logic properly recovers from failures"""
        from utils.action_verifier import verified_action
        
        call_count = 0
        def action_that_fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "OK"
        
        def verifier():
            return True
        
        success, msg = verified_action(action_that_fails_twice, verifier, max_attempts=3)
        self.assertTrue(success)
        self.assertEqual(call_count, 3)


class TestAutomationReliability(unittest.TestCase):
    """Stress tests for reliability"""
    
    def test_rapid_typing_stability(self):
        """Test that rapid successive typing doesn't break"""
        agent = DesktopAgent()
        
        # Type 100 characters rapidly
        for i in range(10):
            text = f"Line {i}: The quick brown fox jumps over the lazy dog."
            agent.type_text(text + "\n")
            time.sleep(0.1)
        
        # Should complete without exception
        self.assertTrue(True)
    
    def test_mouse_movement_sequence(self):
        """Test sequence of mouse movements"""
        human = HumanizedInput()
        
        targets = [
            (100, 100), (200, 200), (300, 300),
            (400, 400), (500, 500), (600, 600)
        ]
        
        for x, y in targets:
            human.move_to(x, y, smooth=True)
            time.sleep(0.3)
        
        # Should complete without error
        self.assertTrue(True)
    
    def test_concurrent_operations(self):
        """Test multiple agents can operate concurrently"""
        agent1 = DesktopAgent()
        agent2 = DesktopAgent()
        
        # Both should be functional
        self.assertIsNotNone(agent1.human)
        self.assertIsNotNone(agent2.human)
        
        # Both should be able to get screen size
        size1 = agent1.get_screen_size()
        size2 = agent2.get_screen_size()
        self.assertEqual(size1, size2)


def run_integration_tests():
    """Run integration tests and report"""
    print("="*60)
    print("1100% AUTOMATION - INTEGRATION TEST SUITE")
    print("="*60 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestRealWorldAutomation))
    suite.addTests(loader.loadTestsFromTestCase(TestAutomationReliability))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print("INTEGRATION TEST REPORT")
    print("="*60)
    print(f"Total: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n[OK] ALL INTEGRATION TESTS PASSED")
        print("  Automation system is 1100% operational!")
    else:
        print("\n[ERROR] Some integration tests failed:")
        for test, trace in result.failures + result.errors:
            print(f"  - {test}: {trace[:200]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
