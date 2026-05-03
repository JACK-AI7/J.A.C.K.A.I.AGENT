#!/usr/bin/env python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    print("Available browsers:", dir(p))
    try:
        browser = p.chromium.launch(channel="chrome", headless=False)
        print("Launched Chrome via channel")
    except Exception as e:
        print(f"Channel launch failed: {e}")
        print("Falling back to default chromium")
        browser = p.chromium.launch(headless=False)
    
    page = browser.new_page()
    page.goto("https://www.youtube.com", wait_until="domcontentloaded")
    time.sleep(4)
    print("Page title:", page.title())
    # Check for video thumbnails
    count = page.locator("ytd-rich-item-renderer").count()
    print("ytd-rich-item-renderer count:", count)
    input("Press Enter to close browser...")
    browser.close()
