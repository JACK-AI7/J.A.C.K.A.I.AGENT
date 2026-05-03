#!/usr/bin/env python
"""Find search input on YouTube via Playwright"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    page = browser.new_page()
    page.goto("https://www.youtube.com", wait_until="domcontentloaded")
    time.sleep(4)
    
    # Use JS to get input elements
    inputs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input'))
            .map(i => ({
                id: i.id || '',
                name: i.name || '',
                type: i.type || '',
                placeholder: i.placeholder || '',
                'aria-label': i.getAttribute('aria-label') || ''
            }));
    }""")
    print("All inputs:")
    for inp in inputs:
        print(f"  id={inp['id']}, name={inp['name']}, type={inp['type']}, placeholder={inp['placeholder']}, aria-label={inp['aria-label']}")
    
    # Focus top bar and press Ctrl+K (YouTube shortcut)
    print("\nTrying keyboard shortcut Ctrl+K to focus search...")
    page.keyboard.press("Control+K")
    time.sleep(1)
    
    # Check if a search overlay appears
    overlay = page.locator("ytd-searchbox")
    print(f"ytd-searchbox count: {overlay.count()}")
    
    # Check if an input appeared with role='combobox'
    combo = page.locator("input[role='combobox']")
    print(f"input[role='combobox] count: {combo.count()}")
    
    input("Enter to quit")
    browser.close()
