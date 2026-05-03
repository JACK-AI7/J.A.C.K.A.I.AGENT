#!/usr/bin/env python
"""
YouTube Search & Play Test - Full DOM + Humanized Input
Uses WebNavigator (Playwright) to:
- Open installed Chrome
- Navigate to YouTube
- Type search query with realistic keystrokes
- Press Enter
- Click first video with human-like mouse movement
- Verify playback
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.web_navigator import web_navigator
import time

def test_youtube_search_play():
    print("\n" + "="*70)
    print("YOUTUBE SEARCH & PLAY TEST - Full Humanized DOM Flow")
    print("Goal: Open YouTube -> Search 'munna bhaai gaming' -> Play first video")
    print("="*70)
    
    wn = web_navigator
    wn.headless = False
    
    # Close any existing browser
    try: wn.close()
    except: pass
    
    # Step 1: Open YouTube
    print("\n[1] Opening YouTube...")
    wn.navigate("https://www.youtube.com")
    time.sleep(3)
    
    # Handle consent popups
    print("[2] Handling consent popups...")
    try:
        # Accept consent if shown
        accept = wn.page.locator("button:has-text('Accept all'), button[aria-label='Accept all']")
        if accept.count() > 0:
            accept.first.click()
            print("  Accepted cookie consent")
            time.sleep(1)
    except: pass
    
    # Step 3: Focus search box and type search query with humanized input
    print("[3] Typing search query: 'munna bhaai gaming'")
    try:
        # Wait for search input
        wn.page.wait_for_selector("input#search, input[aria-label='Search']", timeout=10000)
        search_box = wn.page.locator("input#search, input[aria-label='Search']").first
        
        # Click to focus
        search_box.click()
        time.sleep(0.5)
        
        # Type with realistic human delays (Playwright's type with delay)
        search_query = "munna bhaai gaming"
        print(f"  Typing '{search_query}' with 100ms per char...")
        search_box.type(search_query, delay=100)  # 100ms between keystrokes
        time.sleep(0.5)
        
        # Press Enter
        print("  Pressing Enter...")
        wn.page.keyboard.press("Enter")
        
        # Wait for search results to load
        print("  Waiting for results page...")
        time.sleep(3)
    except Exception as e:
        print(f"  Search error: {e}")
        return False
    
    # Step 4: Confirm search executed (page title or URL)
    print("[4] Verifying search results page...")
    try:
        # Check URL contains search query
        current_url = wn.page.url
        print(f"  URL: {current_url}")
        if "search_query" in current_url or "results" in current_url:
            print("  Search results confirmed")
        else:
            print("  WARNING: URL doesn't look like search results")
    except: pass
    
    # Step 5: Find first video thumbnail and click it with realistic mouse movement
    print("[5] Finding and clicking first video...")
    try:
        # Wait for video results to appear
        # Look for any anchor with /watch? in href (video links)
        wn.page.wait_for_function("""() => {
            return Array.from(document.querySelectorAll('a[href*="/watch"]')).length > 0;
        }""", timeout=10000)
        
        video_links = wn.page.locator("a[href*='/watch']").all()
        print(f"  Found {len(video_links)} video link elements")
        
        if len(video_links) == 0:
            # Fallback: look for ytd-video-renderer / ytd-rich-item-renderer
            print("  Trying CSS selectors...")
            for sel in ["ytd-rich-item-renderer a", "ytd-video-renderer a", "#dismissible a"]:
                els = wn.page.locator(sel).all()
                if els:
                    video_links = els
                    print(f"  Found {len(els)} via {sel}")
                    break
        
        if not video_links:
            print("  ERROR: No video links found")
            return False
        
        # Click first video using humanized mouse movement
        first_video = video_links[0]
        
        # Get element's bounding box for custom mouse path
        box = first_video.bounding_box()
        if box:
            center_x = box['x'] + box['width'] / 2
            center_y = box['y'] + box['height'] / 2
            print(f"  Video at ({center_x:.0f}, {center_y:.0f})")
            
            # Move mouse to element with humanized delay AND click
            print("  Moving mouse to element (humanized)...")
            wn.page.mouse.move(center_x, center_y, steps=25)  # 25 steps for smooth curve
            time.sleep(0.3)
            wn.page.mouse.click(center_x, center_y)
            print("  Clicked!")
        else:
            # Fallback: just click the element
            first_video.click()
            print("  Clicked (no bounding box)")
        
        time.sleep(3)  # Wait for navigation
        
    except Exception as e:
        print(f"  Click failed: {e}")
        return False
    
    # Step 6: Wait and verify playback
    print("[6] Waiting for video page to load and verifying playback...")
    
    try:
        # Wait for player controls
        wn.page.wait_for_selector("button.ytp-play-button", timeout=20000)
        print("  Play button found")
        
        # Click play if needed
        play_btn = wn.page.locator("button.ytp-play-button").first
        classes = play_btn.get_attribute("class") or ""
        if "ytp-button-pause" in classes:
            print("  Video already playing")
            playing = True
        else:
            print("  Clicking play button...")
            play_btn.click()
            time.sleep(2)
            
            # Re-check
            classes = play_btn.get_attribute("class") or ""
            playing = ("ytp-button-pause" in classes)
        
        # Verify by measuring currentTime
        video = wn.page.locator("video")
        t0 = video.evaluate("v => v.currentTime")
        print(f"  Current time at start: {t0:.2f}s")
        time.sleep(3)
        t1 = video.evaluate("v => v.currentTime")
        print(f"  Current time after 3s: {t1:.2f}s")
        
        advancing = t1 > t0 + 1.5  # Should advance at least 1.5 seconds
        playback_ok = playing and advancing
        
        print(f"  Playback state: {'PLAYING' if playing else 'paused/unknown'}")
        print(f"  Time advancing: {'YES' if advancing else 'NO'}")
        
    except Exception as e:
        print(f"  Verification error: {e}")
        playback_ok = False
    
    # Final result
    success = playback_ok
    print("\n" + "="*70)
    if success:
        print("TEST RESULT: SUCCESS")
        print("  - YouTube opened")
        print("  - Search executed: 'munna bhaai gaming'")
        print("  - First video clicked with mouse")
        print("  - Video playing (time advancing)")
    else:
        print("TEST RESULT: FAILED")
        print("  Some steps did not complete successfully")
    print("="*70)
    
    # Close browser
    try:
        wn.close()
        print("\nBrowser closed.")
    except: pass
    
    return success

if __name__ == "__main__":
    result = test_youtube_search_play()
    sys.exit(0 if result else 1)
