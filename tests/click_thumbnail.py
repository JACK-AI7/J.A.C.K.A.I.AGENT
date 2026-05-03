#!/usr/bin/env python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    page = browser.new_page()
    page.goto("https://www.youtube.com", wait_until="domcontentloaded")
    time.sleep(4)
    
    # Look for a#thumbnail anchors
    thumbnails = page.locator("a#thumbnail")
    count = thumbnails.count()
    print(f"Found {count} a#thumbnail elements")
    
    if count > 0:
        # Print href of first few
        for i in range(min(3, count)):
            href = thumbnails.nth(i).get_attribute("href")
            print(f"  [{i}] href={href}")
        # Click the first one that contains /watch
        target = None
        for i in range(count):
            href = thumbnails.nth(i).get_attribute("href")
            if href and "/watch" in href:
                target = thumbnails.nth(i)
                break
        if target:
            print(f"Clicking first watch link...")
            target.click()
            time.sleep(4)  # wait for video page
            print("New page title:", page.title())
            # Check for play button
            pause = page.locator("button.ytp-play-button")
            if pause.count() > 0:
                title = pause.first.get_attribute("title")
                print(f"Play button state: {title}")
            else:
                print("No play button found")
        else:
            print("No /watch link found")
    else:
        print("No thumbnails found")
    
    input("Press Enter to close")
    browser.close()
