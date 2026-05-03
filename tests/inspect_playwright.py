#!/usr/bin/env python
"""Quick Playwright inspection of youtube.com"""
import sys, os
sys.path.insert(0, os.path.abspath('.'))

from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.set_viewport_size({"width": 1280, "height": 720})
    
    print("Navigating to https://www.youtube.com")
    page.goto("https://www.youtube.com", wait_until="domcontentloaded")
    time.sleep(4)  # Wait for dynamic loading
    
    # Take a screenshot for reference
    page.screenshot(path="youtube_home.png")
    print("Screenshot saved: youtube_home.png")
    
    # List some selector counts
    selectors = [
        "ytd-rich-item-renderer",
        "ytd-video-renderer", 
        "ytd-grid-video-renderer",
        "#dismissible",
        "ytd-rich-grid-renderer",
        "ytd-rich-item-renderer",
        "a#video-title",
        "ytd-rich-item-renderer h3 a",
        "#content ytd-rich-item-renderer",
    ]
    
    print("\nSelector counts:")
    for sel in selectors:
        count = page.locator(sel).count()
        print(f"  {sel}: {count}")
    
    # Try to get first visible thumbnail text
    print("\nFirst few visible items stats.")
    # List limited
    items = page.locator("ytd-rich-item-renderer").all()
    if not items:
        print("  No ytd-rich-item-renderer found")
        # Maybe they're inside a shadow? Use JS to query
        # Let's count using JS
        count = page.evaluate("""() => {
            return document.querySelectorAll('ytd-rich-item-renderer').length;
        }""")
        print(f"  JS querySelectorAll: {count}")
    else:
        print(f"  Found {len(items)} items")
        # For first item, print its accessible text
        try:
            txt = items[0].inner_text()
            print(f"    First item text: {txt[:80]}")
        except: pass
    
    # Try to see if there are <a id='video-title'> elements anywhere
    vtitles = page.locator("a#video-title").all()
    print(f"\n  a#video-title count: {len(vtitles)}")
    if vtitles:
        for i, el in enumerate(vtitles[:3]):
            print(f"    [{i}] '{el.inner_text()[:60]}'")
    
    browser.close()
    
print("Done.")
