#!/usr/bin/env python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    page = browser.new_page()
    page.goto("https://www.youtube.com", wait_until="domcontentloaded")
    time.sleep(6)
    
    # Use JS to collect all web components / ytd-* tags
    tags = page.evaluate("""() => {
        const els = document.querySelectorAll('*');
        const tagSet = new Set();
        els.forEach(el => {
            if (el.tagName && el.tagName.startsWith('YT-')) tagSet.add(el.tagName.toLowerCase());
        });
        return Array.from(tagSet).sort();
    }""")
    print("YT- tags found:", tags[:30])
    
    # Also count any element that is a video tile: maybe ytd-rich-item-renderer but zero, so what's used?
    # Check all elements with id containing 'video' or 'title' etc.
    candidates = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('[id*="video"], [id*="title"], [id*="thumbnail"]'))
                    .map(el => el.tagName.toLowerCase() + '#' + el.id)
                    .slice(0, 20);
    }""")
    print("Elements with video/title/thumbnail in id:", candidates)
    
    # Print some outerHTML of #dismissible
    dismiss = page.locator("#dismissible")
    if dismiss.count() > 0:
        print("dismissible outerHTML snippet:")
        print(dismiss.first().inner_text()[:200])
    
    # Look for anchor tags with href containing '/watch'
    watch_links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a[href*="/watch"]'))
                    .slice(0, 5)
                    .map(a => a.href + ' | ' + (a.innerText || '').trim().slice(0,50));
    }""")
    print("First 5 watch links:", watch_links)
    
    input("Press Enter to quit")
    browser.close()
