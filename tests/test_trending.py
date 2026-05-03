#!/usr/bin/env python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    page = browser.new_page()
    
    print("Navigating to YouTube Trending...")
    page.goto("https://www.youtube.com/feed/trending", wait_until="domcontentloaded")
    time.sleep(5)
    
    print("Page title:", page.title())
    
    # Check for video links
    links = page.locator("a[href*='/watch']")
    count = links.count()
    print(f"Found {count} /watch links")
    
    if count > 0:
        # Print first few hrefs
        for i in range(min(5, count)):
            href = links.nth(i).get_attribute("href")
            print(f"  [{i}] {href}")
        # Click first link (skip possible duplicate? but okay)
        print("\nClicking first link...")
        links.nth(0).click()
        time.sleep(4)
        print("New page title:", page.title())
        # Check for play button
        play_btn = page.locator("button.ytp-play-button")
        if play_btn.count() > 0:
            title = play_btn.first.get_attribute("title")
            print(f"Play button: {title}")
        else:
            print("Play button not found")
    else:
        print("No watch links found")
    
    input("Press Enter to close")
    browser.close()
