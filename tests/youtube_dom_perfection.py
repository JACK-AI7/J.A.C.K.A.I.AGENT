#!/usr/bin/env python
"""
YouTube DOM Automation Test - Best AI Agent (WebNavigator)
Uses Playwright (100% DOM accuracy) to open YouTube and play a video.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.web_navigator import web_navigator
import time

def test_youtube_play_video():
    print("\n" + "="*70)
    print("YOUTUBE DOM AUTOMATION - 100% ACCURACY")
    print("="*70)
    
    # Close any existing instance to start fresh
    try: web_navigator.close()
    except: pass
    
    wn = web_navigator
    wn.headless = False
    
    # Direct video URL (first ever YouTube video)
    video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    print("\n[1] Navigating to video...")
    wn.navigate(video_url)
    time.sleep(3)
    
    # Handle consent
    print("[2] Handling consent...")
    try:
        consent = wn.page.locator("button[aria-label='Accept all']")
        if consent.count() > 0:
            consent.first.click()
            print("  Accepted cookies")
            time.sleep(1)
    except: pass
    
    # Dismiss sign-in popup if present
    print("[3] Dismissing pop-ups...")
    try:
        for txt in ["No thanks", "Not now"]:
            btn = wn.page.locator(f"text={txt}")
            if btn.count() > 0:
                btn.first.click()
                print(f"  Clicked '{txt}'")
                time.sleep(1)
                break
    except: pass
    
    # Wait for player
    print("[4] Waiting for video player...")
    try:
        wn.page.wait_for_selector("video", timeout=15000)
        print("  <video> element present")
    except Exception as e:
        print(f"  Video element not found: {e}")
        return False
    
    # Ensure video is playing (click play if needed)
    print("[5] Ensuring playback...")
    try:
        play_btn = wn.page.locator("button.ytp-play-button").first
        # Click regardless - if already playing, this will toggle to pause then back? 
        # Safer: check current state via class or aria-label
        btn_classes = play_btn.get_attribute("class") or ""
        if "ytp-button-pause" in btn_classes:
            print("  Already playing (pause class present)")
            playing = True
        else:
            print("  Clicking play button")
            play_btn.click()
            time.sleep(2)  # wait for buffering
            # Could also press space on video element
    except Exception as e:
        print(f"  Play button error: {e}")
    
    # Verify by measuring currentTime
    print("[6] Verifying playback by time advancement...")
    try:
        video = wn.page.locator("video")
        t0 = video.evaluate("v => v.currentTime")
        print(f"  Time 0: {t0:.2f}s")
        time.sleep(3)
        t1 = video.evaluate("v => v.currentTime")
        print(f"  Time after 3s: {t1:.2f}s")
        advancing = t1 > t0 + 1.0
    except Exception as e:
        print(f"  Measurement error: {e}")
        return False
    
    success = advancing
    print("\n" + "="*70)
    if success:
        print("RESULT: SUCCESS - Video is playing")
    else:
        print("RESULT: FAIL - Playback not advancing")
    print("="*70)
    
    return success

if __name__ == "__main__":
    ok = test_youtube_play_video()
    try:
        web_navigator.close()
        print("Browser closed.")
    except: pass
    sys.exit(0 if ok else 1)
