#!/usr/bin/env python
"""
YouTube Automation Test - Full End-to-End
Tests: Open YouTube → Play first video → Subscribe to channel
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'agents'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'utils'))

from agents.desktop_agent import DesktopAgent
from agents.system_controller import SystemController
from agents.visual_orchestrator import VisualOrchestrator
from core.nexus_bridge import get_signals


def test_youtube_full_flow():
    """
    Complete YouTube automation test:
    1. Open browser to YouTube
    2. Find and click first video
    3. Click subscribe button
    """
    print("\n" + "="*60)
    print("YOUTUBE AUTOMATION TEST - 1100% Human-Like")
    print("="*60)
    
    # Initialize agents
    da = DesktopAgent()
    sc = SystemController()
    signals = get_signals()
    
    # Step 1: Open browser to YouTube
    print("\n[STEP 1] Opening browser to YouTube...")
    result = da.open_application("chrome")
    print(f"  DesktopAgent: {result}")
    
    if "At your command" not in result and "Error" not in result:
        time.sleep(2)
        # Try typing URL
        da.type_text("https://www.youtube.com")
        da.human.hotkey('ctrl', 'enter')
        print("  Typed URL and pressed Ctrl+Enter")
    else:
        print("  Chrome launched, waiting for it to open...")
    
    time.sleep(4)  # Wait for browser to open
    
    # Step 2: Navigate to YouTube if not already there
    print("\n[STEP 2] Navigating to YouTube...")
    try:
        from agents.web_navigator import web_navigator
        result = web_navigator.navigate("youtube.com")
        print(f"  WebNavigator: {result}")
        time.sleep(3)  # Wait for page load
    except Exception as e:
        print(f"  WebNavigator not available: {e}")
        print("  Using keyboard navigation instead...")
        da.human.hotkey('ctrl', 'l')  # Focus address bar
        time.sleep(0.5)
        da.type_text("youtube.com")
        da.human.hotkey('enter')
        time.sleep(4)
    
    # Step 3: Find and click first video using visual orchestrator
    print("\n[STEP 3] Finding and clicking first video...")
    
    # Try multiple strategies
    strategies = [
        "first video thumbnail",
        "video player",
        "ytd-video-renderer",  # YouTube CSS selector
        "play button",
        "video title"
    ]
    
    video_clicked = False
    for strategy in strategies:
        print(f"  Trying strategy: '{strategy}'")
        try:
            if "ytd-" in strategy or strategy.startswith("#") or strategy.startswith("."):
                # CSS selector - use web_navigator click_by_selector
                result = web_navigator.click_by_selector(strategy)
            else:
                # Text-based - use visual orchestrator
                orch = VisualOrchestrator()
                result = orch.smart_click(strategy)
            
            print(f"    Result: {result}")
            if "Clicked" in result or "Success" in result or "Found" in result:
                video_clicked = True
                break
        except Exception as e:
            print(f"    Strategy failed: {e}")
            continue
    
    if not video_clicked:
        print("  ⚠ Could not click video automatically. Trying manual coordinate click...")
        # Fallback: Try to find video coordinates via vision
        try:
            coords = sc.visual_locate("video")
            if isinstance(coords, dict):
                sc.locate_and_click(coords['x'], coords['y'])
                print(f"  Clicked at vision-detected coordinates: ({coords['x']}, {coords['y']})")
                video_clicked = True
            else:
                print(f"  Vision search failed: {coords}")
        except Exception as e:
            print(f"  Vision fallback failed: {e}")
    
    time.sleep(3)  # Wait for video to load/play
    
    # Step 4: Subscribe to channel
    print("\n[STEP 4] Subscribing to channel...")
    
    # Subscription strategies
    sub_strategies = [
        "subscribe button",
        "subscribe",
        "SUBSCRIBE",
        "button text: subscribe",
        "ytd-subscribe-button-renderer"
    ]
    
    subscribed = False
    for strategy in sub_strategies:
        print(f"  Trying subscribe: '{strategy}'")
        try:
            if "ytd-" in strategy or strategy.startswith("#"):
                result = web_navigator.click_by_selector(strategy)
            else:
                orch = VisualOrchestrator()
                result = orch.smart_click(strategy)
            
            print(f"    Result: {result}")
            if "Clicked" in result or "Subscribed" in result or "Success" in result:
                subscribed = True
                break
        except Exception as e:
            print(f"    Strategy failed: {e}")
            continue
    
    if not subscribed:
        print("  ⚠ Could not auto-subscribe. Subscription may require login.")
    
    # Step 5: Verify video is playing
    print("\n[STEP 5] Verifying video playback...")
    time.sleep(2)
    
    # Check if video player is visible
    try:
        # Use vision to check for play/pause button
        play_btn = sc.visual_locate("pause")
        if isinstance(play_btn, dict):
            print("  ✓ Video appears to be playing (pause button visible)")
        else:
            # Look for time indicator (01:23 / 10:45)
            time_display = sc.visual_locate(":")
            if isinstance(time_display, dict):
                print("  ✓ Video appears to be playing (time display visible)")
            else:
                print("  ⚠ Could not verify video playback")
    except Exception as e:
        print(f"  Verification error: {e}")
    
    # Final status
    print("\n" + "="*60)
    print("YOUTUBE TEST COMPLETE")
    print("="*60)
    print(f"Video Clicked: {'[OK]' if video_clicked else '[FAIL]'}")
    print(f"Subscribed: {'[OK]' if subscribed else '[FAIL] (may need login)'}")
    print("\nNote: Full automation requires:")
    print("  1. Chrome installed and accessible")
    print("  2. YouTube loaded completely")
    print("  3. Visual AI (EasyOCR + Ollama) for element detection")
    print("  4. Login for subscription capability")
    print("="*60)
    
    return {
        'video_clicked': video_clicked,
        'subscribed': subscribed,
        'notes': 'Requires EasyOCR + Ollama for best results'
    }


def test_youtube_with_web_navigator_only():
    """Simplified test using only web_navigator (DOM-based)"""
    print("\n" + "="*60)
    print("YOUTUBE WEB NAVIGATOR TEST")
    print("="*60)
    
    try:
        from agents.web_navigator import web_navigator
        
        print("\n1. Navigating to YouTube...")
        result = web_navigator.navigate("youtube.com")
        print(f"  {result}")
        time.sleep(3)
        
        print("\n2. Getting page summary...")
        summary = web_navigator.get_page_summary()
        print(f"  Page: {summary[:100]}...")
        
        print("\n3. Extracting interactive elements...")
        elements = web_navigator.get_dom_elements(max_elements=20)
        print(f"  {elements[:500]}...")
        
        print("\n4. Searching for video thumbnails...")
        # Try to find video elements by CSS selectors
        video_selectors = [
            "ytd-video-renderer",
            "ytd-grid-video-renderer",
            "#dismissible",
            "a#video-title"
        ]
        
        for selector in video_selectors:
            try:
                count = web_navigator.page.locator(selector).count()
                print(f"  Selector '{selector}': {count} elements")
                if count > 0:
                    web_navigator.click_by_selector(selector)
                    print(f"  [OK] Clicked first video using '{selector}'")
                    break
            except Exception as e:
                print(f"  Selector '{selector}' failed: {e}")
        
        time.sleep(3)
        
        print("\n5. Looking for subscribe button...")
        # Common YouTube selectors for subscribe
        sub_selectors = [
            "ytd-subscribe-button-renderer",
            "#subscribe-button",
            "paper-button[aria-label*='subscribe']",
            "ytd-button-renderer"
        ]
        
        for selector in sub_selectors:
            try:
                count = web_navigator.page.locator(selector).count()
                print(f"  Selector '{selector}': {count} elements")
                if count > 0:
                    web_navigator.click_by_selector(selector)
                    print(f"  [OK] Clicked subscribe using '{selector}'")
                    break
            except Exception as e:
                print(f"  Selector '{selector}' failed: {e}")
        
        print("\n[OK] Web Navigator test completed")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Web Navigator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("YouTube Automation Test Suite")
    print("="*60)
    print("\nChoose test mode:")
    print("  1. Full test (DesktopAgent + VisualOrchestrator)")
    print("  2. Web navigator only (DOM-based)")
    print("  3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_youtube_full_flow()
    elif choice == "2":
        test_youtube_with_web_navigator_only()
    elif choice == "3":
        test_youtube_full_flow()
        print("\n" + "="*60)
        print("NOW TESTING WEB NAVIGATOR MODE")
        print("="*60)
        test_youtube_with_web_navigator_only()
    else:
        print("Invalid choice. Running full test...")
        test_youtube_full_flow()
    
    print("\nTest complete. Press Enter to exit...")
    input()
