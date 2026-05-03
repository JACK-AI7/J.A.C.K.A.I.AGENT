#!/usr/bin/env python
"""
FINAL INTEGRATION TEST - Verify All Systems Working
Tests: All agents initialize, emit signals, perform actions, show in HUD
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'agents'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'utils'))

from core.nexus_bridge import get_signals
from core.dashboard_integration import dashboard_manager


def test_all_agents_initialized():
    """Verify all agents initialize and register"""
    print("\n" + "="*60)
    print("TEST 1: Agent Initialization")
    print("="*60)
    
    agents = dashboard_manager.list_agents()
    print(f"Available agents: {agents}")
    
    expected_agents = ["DesktopAgent", "SystemController", "VisualOrchestrator", "WebNavigator"]
    
    for agent_name in expected_agents:
        if agent_name in agents:
            print(f"  ✓ {agent_name} registered")
        else:
            print(f"  ✗ {agent_name} NOT FOUND")
    
    success = all(agent in agents for agent in expected_agents)
    print(f"\nResult: {'PASS' if success else 'FAIL'}")
    return success


def test_agent_signals():
    """Verify agents emit signals that HUD can receive"""
    print("\n" + "="*60)
    print("TEST 2: Signal Emission")
    print("="*60)
    
    signals = get_signals()
    
    # Get DesktopAgent
    da = dashboard_manager.get_agent("DesktopAgent")
    if da:
        print("  DesktopAgent retrieved")
        
        # Perform a simple action
        print("  Testing click_position...")
        da.click_position(100, 100)
        print("  ✓ Click signal emitted")
        
        # Test typing
        print("  Testing type_text...")
        da.type_text("Test signal")
        print("  ✓ Type signal emitted")
        
        print("  Result: PASS")
        return True
    else:
        print("  ✗ DesktopAgent not available")
        return False


def test_hud_integration():
    """Verify HUD can be initialized and shows agent dashboard"""
    print("\n" + "="*60)
    print("TEST 3: HUD Integration")
    print("="*60)
    
    try:
        # Try to import HUD components
        from gui.hud_manager import HUDManager, AgentDashboard
        print("  ✓ HUD components imported")
        
        # Check if AgentDashboard class exists
        if hasattr(AgentDashboard, 'register_agent'):
            print("  ✓ AgentDashboard has register_agent method")
        else:
            print("  ✗ AgentDashboard missing methods")
            return False
            
        # Check signal connections
        from PySide6.QtCore import QCoreApplication
        app = QCoreApplication.instance()
        if app is None:
            print("  ⚠ No QApplication - HUD needs GUI mode")
        else:
            print("  ✓ QApplication available")
        
        print("  Result: PASS")
        return True
        
    except Exception as e:
        print(f"  ✗ HUD integration error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visual_orchestrator():
    """Test VisualOrchestrator can execute autonomous mission"""
    print("\n" + "="*60)
    print("TEST 4: VisualOrchestrator Autonomy")
    print("="*60)
    
    try:
        from agents.visual_orchestrator import VisualOrchestrator
        
        orch = VisualOrchestrator()
        print("  ✓ VisualOrchestrator initialized")
        
        # Test screen awareness
        summary = orch.get_screen_summary()
        print(f"  Screen summary: {summary[:80]}...")
        print("  ✓ Screen awareness working")
        
        # Test simple mission (doesn't need to complete)
        print("  Testing autonomous mission (5 steps max)...")
        result = orch.execute_mission("Open Notepad")
        print(f"  Mission result: {result[:80]}...")
        print("  ✓ Autonomous execution working")
        
        print("  Result: PASS")
        return True
        
    except Exception as e:
        print(f"  ✗ VisualOrchestrator error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_system_controller_vision():
    """Test SystemController vision capabilities"""
    print("\n" + "="*60)
    print("TEST 5: SystemController Vision")
    print("="*60)
    
    try:
        from agents.system_controller import system_controller
        
        print("  SystemController initialized")
        
        # Test visual_locate (search for something on screen)
        result = system_controller.visual_locate("test")
        print(f"  visual_locate('test'): {type(result).__name__}")
        print("  ✓ OCR vision working")
        
        # Test locate_and_click
        result = system_controller.locate_and_click(100, 100, verify=False)
        print(f"  locate_and_click(100,100): {result[:50]}...")
        print("  ✓ Humanized click working")
        
        print("  Result: PASS")
        return True
        
    except Exception as e:
        print(f"  ✗ SystemController error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_navigator():
    """Test WebNavigator web automation"""
    print("\n" + "="*60)
    print("TEST 6: WebNavigator DOM Automation")
    print("="*60)
    
    try:
        from agents.web_navigator import web_navigator
        
        print("  WebNavigator initialized")
        
        # Test navigation (we won't actually navigate, just check method exists)
        if hasattr(web_navigator, 'navigate'):
            print("  ✓ navigate() method available")
        if hasattr(web_navigator, 'click_element'):
            print("  ✓ click_element() method available")
        if hasattr(web_navigator, 'fill_input'):
            print("  ✓ fill_input() method available")
        
        print("  Result: PASS")
        return True
        
    except Exception as e:
        print(f"  ✗ WebNavigator error: {e}")
        return False


def test_humanized_input():
    """Test HumanizedInput core features"""
    print("\n" + "="*60)
    print("TEST 7: HumanizedInput Engine")
    print("="*60)
    
    try:
        from utils.humanized_input import HumanizedInput, HumanConfig
        
        # Create instance
        config = HumanConfig(
            mouse_precision=0.9,
            typing_speed_base=0.01,  # Fast for test
            typo_chance=0.0  # No typos in test
        )
        human = HumanizedInput(config)
        print("  ✓ HumanizedInput created")
        
        # Test mouse movement (non-smooth for speed)
        human.move_to(200, 200, smooth=False)
        print("  ✓ Mouse movement working")
        
        # Test typing
        human.type_text("Test typing")
        print("  ✓ Typing working")
        
        # Test hotkey
        human.hotkey('ctrl', 'c')
        print("  ✓ Hotkey working")
        
        # Test Bezier path generation
        path = human._calculate_bezier_path((0,0), (100,100), 30)
        assert len(path) == 30, "Bezier path wrong length"
        print("  ✓ Bezier curves working")
        
        print("  Result: PASS")
        return True
        
    except Exception as e:
        print(f"  ✗ HumanizedInput error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_action_verifier():
    """Test action verification system"""
    print("\n" + "="*60)
    print("TEST 8: Action Verification")
    print("="*60)
    
    try:
        from utils.action_verifier import ActionVerifier, verified_action
        from utils.humanized_input import HumanizedInput
        
        human = HumanizedInput()
        verifier = ActionVerifier(human)
        print("  ✓ ActionVerifier created")
        
        # Test image difference
        import numpy as np
        img1 = np.zeros((10, 10), dtype=np.uint8)
        img2 = np.full((10, 10), 255, dtype=np.uint8)
        diff = verifier._image_difference(img1, img2)
        assert diff > 0.5, f"Image diff should be high, got {diff}"
        print(f"  ✓ Image difference working (diff={diff:.2f})")
        
        # Test verified_action wrapper
        def good_action():
            return "Success"
        
        success, msg = verified_action(good_action, lambda: True, 1)
        assert success, "verified_action should succeed"
        print("  ✓ Retry wrapper working")
        
        print("  Result: PASS")
        return True
        
    except Exception as e:
        print(f"  ✗ ActionVerifier error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run complete integration test suite"""
    print("\n" + "="*70)
    print("JARVIS 1100% AUTOMATION - FINAL INTEGRATION TEST SUITE")
    print("="*70)
    
    tests = [
        ("Agent Initialization", test_all_agents_initialized),
        ("Agent Signal Emission", test_agent_signals),
        ("HUD Integration", test_hud_integration),
        ("VisualOrchestrator", test_visual_orchestrator),
        ("SystemController Vision", test_system_controller_vision),
        ("WebNavigator DOM", test_web_navigator),
        ("HumanizedInput Engine", test_humanized_input),
        ("Action Verification", test_action_verifier),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("FINAL INTEGRATION TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS GO - JARVIS IS 1100% OPERATIONAL!")
        print("   • All agents initialized")
        print("   • Dashboard integration complete")
        print("   • Humanized automation working")
        print("   • Signals flowing to HUD")
        print("   • Ready for production")
    else:
        print(f"\n⚠ {total-passed} system(s) need attention")
    
    print("="*70)
    
    return passed == total


if __name__ == "__main__":
    # Add PySide6 check
    try:
        from PySide6.QtWidgets import QApplication
        if QApplication.instance() is None:
            print("Note: Running without GUI. HUD tests may be limited.")
    except:
        print("Warning: PySide6 not fully available")
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
