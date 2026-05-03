#!/usr/bin/env python
"""
One-shot YouTube automation test - Web Navigator only
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import time
from agents.web_navigator import web_navigator

def test_youtube():
    print("\n" + "="*60)
    print("YOUTUBE AUTOMATION TEST - Web Navigator Mode")
    print("="*60)
    
    # Navigate to YouTube
    print("\n[1] Navigating to YouTube...")
    result = web_navigator.navigate("youtube.com")
    print(f"  Result: {result}")
    time.sleep(3)
    
    # Get page info
    print("\n[2] Getting page title...")
    title = web_navigator.page.title()
    print(f"  Page title: {title}")
    
    # Search for video elements
    print("\n[3] Searching for video thumbnails...")
    video_selectors = [
        "ytd-video-renderer",
        "ytd-grid-video-renderer",
        "#dismissible",
        "a#video-title",
        "h3#video-title"
    ]
    
    clicked = False
    for selector in video_selectors:
        try:
            count = web_navigator.page.locator(selector).count()
            print(f"  Selector '{selector}': {count} elements")
            if count > 0:
                web_navigator.click_by_selector(selector)
                print(f"  SUCCESS: Clicked first video using '{selector}'")
                clicked = True
                break
        except Exception as e:
            print(f"  Selector '{selector}' error: {e}")
    
    time.sleep(3)
    
    # Check for video playback
    print("\n[4] Verifying video playback...")
    if clicked:
        try:
            # Look for video player element
            video_count = web_navigator.page.locator("video").count()
            print(f"  Video elements found: {video_count}")
            if video_count > 0:
                print("  SUCCESS: Video player is present")
            else:
                print("  WARNING: No video element detected")
        except Exception as e:
            print(f"  Verification error: {e}")
    else:
        print("  SKIPPED: No video was clicked")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print(f"Video clicked: {'YES' if clicked else 'NO'}")
    print("="*60)
    
    return clicked

if __name__ == "__main__":
    test_youtube()
