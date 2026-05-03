#!/usr/bin/env python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    page = browser.new_page()
    page.goto("https://www.youtube.com", wait_until="domcontentloaded")
    time.sleep(4)
    
    # Search for input elements
    inputs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input'))
            .map(i => ({
                id: i.id,
                type: i.type,
                name: i.name,
                'aria-label': i.getAttribute('aria-label'),
                placeholder: i.placeholder
            }))
            .filter(i => i.type === 'text' || i.placeholder || i['aria-label'])
            .slice(0, 10);
    }""")
    print("Text inputs found:")
    for i, inp in enumerate(inputs):
        print(f"  [{i}] id={inp['id']}, type={inp['type']}, aria-label={inp['aria-label']}")
    
    # Try the search input
    search_input = page.locator("input#search")
    if search_input.count() > 0:
        print("\nSearch input #search exists")
        print("  placeholder:", search_input.get_attribute("placeholder"))
    else:
        # Try alternative
        alts = ["input[name='search_query']", "input[aria-label*='search']", "#search"]
        for alt in alts:
            els = page.locator(alt).all()
            if els:
                print(f"\nFound via '{alt}': {els[0].get_attribute('outerHTML')[:200]}")
                break
        else:
            print("\nSearch input not found - inspecting top bar")
            topbar = page.locator("ytd-searchbox")
            if topbar.count() > 0:
                print("  ytd-searchbox exists")
    
    input("Press Enter to quit")
    browser.close()
