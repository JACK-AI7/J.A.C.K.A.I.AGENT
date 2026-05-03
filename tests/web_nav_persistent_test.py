#!/usr/bin/env python
"""Test WebNavigator with Chrome persistent context (logged-in)"""
import sys, os
sys.path.insert(0, os.path.abspath('.'))

from agents.web_navigator import web_navigator
import time

def test_persistent():
    print("=== WebNavigator Persistent Profile Test ===\n")
    
    # Close any existing
    try: web_navigator.close()
    except: pass
    
    # Navigate to YouTube - should keep logged-in state
    print("Navigating to YouTube...")
    web_navigator.navigate("https://www.youtube.com")
    time.sleep(3)
    
    # Try to access account menu (visible only if logged in)
    print("\nChecking if logged in...")
    try:
        # Look for avatar button (sign-in indicator)
        avatar = web_navigator.page.locator("button#avatar, img#img, [aria-label='Account']")
        count = avatar.count()
        print(f"Avatar elements found: {count}")
        if count > 0:
            print("User appears to be logged in (avatar visible)")
        else:
            print("No avatar detected - might be logged out or UIA hidden")
    except Exception as e:
        print(f"Check error: {e}")
    
    # Now try search and play using DOM methods
    print("\nAttempting search & play...")
    result = web_navigator.type_in_selector("input[name='search_query']", "munna bhaai gaming")
    print(f"  {result}")
    web_navigator.page.keyboard.press("Enter")
    time.sleep(3)
    
    # Click first video
    videos = web_navigator.page.locator("a[href*='/watch']")
    if videos.count() > 0:
        box = videos.first.bounding_box()
        if box:
            cx = box['x'] + box['width']/2
            cy = box['y'] + box['height']/2
            print(f"  Clicking video at ({cx:.0f},{cy:.0f})")
            web_navigator.page.mouse.move(cx, cy, steps=20)
            web_navigator.page.mouse.click(cx, cy)
            time.sleep(4)
            # Verify playback
            t0 = web_navigator.page.evaluate("document.querySelector('#movie_player video').currentTime")
            time.sleep(3)
            t1 = web_navigator.page.evaluate("document.querySelector('#movie_player video').currentTime")
            print(f"  Playback: {t0:.1f}s -> {t1:.1f}s")
            if t1 > t0 + 2:
                print("  SUCCESS: Video playing")
            else:
                print("  WARNING: Video not advancing")
    else:
        print("  ERROR: No video links found")
    
    # Close
    web_navigator.close()
    print("\nBrowser closed. Test complete.")

if __name__ == "__main__":
    test_persistent()
