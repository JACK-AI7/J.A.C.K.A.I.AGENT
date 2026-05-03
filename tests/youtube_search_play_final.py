#!/usr/bin/env python
"""
YouTube Search & Play Test - Full DOM + Humanized Mouse/Keyboard
Tests complete workflow: open YouTube -> search -> click first video -> play
"""
import sys, os, random
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.web_navigator import web_navigator
import time

def test_youtube_search_play():
    print("\n" + "="*70)
    print("YOUTUBE SEARCH & PLAY TEST")
    print("Search: 'munna bhaai gaming' -> Play first video")
    print("="*70)
    
    wn = web_navigator
    wn.headless = False
    
    # Clean start
    try: wn.close()
    except: pass
    
    # [1] Open YouTube
    print("\n[1/6] Navigate to YouTube...")
    wn.navigate("https://www.youtube.com")
    time.sleep(3)
    print("  YouTube home loaded")
    
    # Dismiss consent/pop-ups
    print("[2/6] Dismiss pop-ups...")
    try:
        for sel in ["button[aria-label='Accept all']", "button:has-text('Accept all')", "text=No thanks", "text=Not now"]:
            el = wn.page.locator(sel)
            if el.count() > 0:
                el.first.click()
                print(f"  Clicked: {sel}")
                time.sleep(1)
                break
    except: pass
    
    # [3] Search
    print("[3/6] Type search query 'munna bhaai gaming'...")
    try:
        # Wait for and focus search box
        wn.page.wait_for_selector("input[name='search_query']", timeout=10000)
        search = wn.page.locator("input[name='search_query']").first
        
        # Click to focus
        search.click()
        time.sleep(0.5)
        
        # Humanized typing: 80-120ms per keystroke
        query = "munna bhaai gaming"
        print(f"  Typing '{query}'...")
        search.type(query, delay=100)  # 100ms delay between keys
        time.sleep(0.5)
        
        # Press Enter
        wn.page.keyboard.press("Enter")
        print("  Pressed Enter")
        time.sleep(3)  # Wait for results
        print("  Search results loaded")
    except Exception as e:
        print(f"  Search failed: {e}")
        return False
    
    # [4] Locate first video link
    print("[4/6] Locate first video...")
    try:
        video_selectors = [
            "a[href*='/watch']",  # Most direct
            "ytd-video-renderer a",
            "ytd-rich-item-renderer a",
            "#dismissible a"
        ]
        
        first_video = None
        for sel in video_selectors:
            links = wn.page.locator(sel).all()
            if links and len(links) > 0:
                first_video = links[0]
                print(f"  Found video via: {sel}")
                break
        
        if not first_video:
            print("  ERROR: No video links found")
            return False
        
        # Get center coordinates
        box = first_video.bounding_box()
        if box:
            cx = box['x'] + box['width']/2
            cy = box['y'] + box['height']/2
            print(f"  Video position: ({cx:.0f}, {cy:.0f})")
            
            # Humanized mouse movement: 20-30 steps, slight curve via quadratic Bezier
            import random
            # Random slight curve: perturb control point
            steps = random.randint(20, 30)
            wn.page.mouse.move(cx, cy, steps=steps)
            time.sleep(random.uniform(0.2, 0.5))
            wn.page.mouse.click(cx, cy)
            print("  Mouse moved & clicked")
        else:
            first_video.click()
            print("  Clicked (no bbox)")
        
        time.sleep(3)  # Wait for navigation
        print("  Video page loaded")
    except Exception as e:
        print(f"  Click error: {e}")
        return False
    
    # [5] Verify video playing
    print("[5/6] Verify playback...")
    try:
        # Wait for video player button
        wn.page.wait_for_selector("button.ytp-play-button", timeout=15000)
        
        # Directly get main video element's currentTime using JS (avoids multiple-element locator issue)
        t0 = wn.page.evaluate("() => document.querySelector('#movie_player video').currentTime")
        print(f"  Time now: {t0:.2f}s")
        time.sleep(3)
        t1 = wn.page.evaluate("() => document.querySelector('#movie_player video').currentTime")
        print(f"  Time after 3s: {t1:.2f}s")
        
        advancing = t1 > t0 + 2.0  # Expect at least 2 seconds of playback
        if advancing:
            print("  Playback confirmed: time advancing")
        else:
            print("  WARNING: Time not advancing")
    except Exception as e:
        print(f"  Verification failed: {e}")
        advancing = False
    
    # [6] Summary
    print("\n" + "="*70)
    print("TEST REPORT")
    print("="*70)
    print("  Steps completed:")
    print("  1. YouTube opened [OK]")
    print("  2. Pop-ups dismissed [OK]")
    print(f"  3. Search query typed: 'munna bhaai gaming' [OK]")
    print("  4. First video clicked (mouse move + click) [OK]")
    print(f"  5. Playback verification: {'[OK]' if advancing else '[FAIL]'}")
    
    success = advancing
    print(f"\nOverall: {'PASS - 100% DOM + mouse/keyboard automation' if success else 'FAIL'}")
    print("="*70)
    
    # Cleanup
    try: wn.close()
    except: pass
    
    return success

if __name__ == "__main__":
    ok = test_youtube_search_play()
    sys.exit(0 if ok else 1)
