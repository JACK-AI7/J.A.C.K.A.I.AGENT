#!/usr/bin/env python
"""Debug YouTube DOM selectors"""
import sys, os
sys.path.insert(0, os.path.abspath('.'))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

options = webdriver.ChromeOptions()
options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
options.add_argument("--start-maximized")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

print("Navigating to youtube.com ...")
driver.get("https://www.youtube.com")
time.sleep(5)  # Wait for initial load

# Accept cookies if present
try:
    btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Accept all']")
    btn.click()
    print("  Accepted cookies")
    time.sleep(2)
except:
    pass

print("\nScanning DOM for common YouTube selectors:")
selectors = [
    "ytd-rich-item-renderer",
    "ytd-video-renderer",
    "#dismissible",
    "ytd-rich-grid-renderer",
    "a#video-title",
    "h3#video-title",
    "#video-title",
    "ytd-rich-item-renderer a#thumbnail",
    "ytd-video-renderer a#video-title-link",
    "ytd-rich-item-renderer h3 a",
]
for sel in selectors:
    try:
        count = driver.find_elements(By.CSS_SELECTOR, sel).__len__()
        print(f"  {sel}: {count} elements")
    except Exception as e:
        print(f"  {sel}: ERROR - {e}")

# Print page title
print(f"\nPage title: {driver.title}")

# Try to get first video title text
print("\nAttempting to locate first video title element...")
candidates = [
    "a#video-title",
    "ytd-video-renderer a#video-title",
    "ytd-rich-item-renderer h3 a",
    "#video-title-link",
]
for cand in candidates:
    try:
        el = driver.find_element(By.CSS_SELECTOR, cand)
        print(f"  Found via {cand}: text='{el.text[:80]}'")
        # Try click
        el.click()
        print(f"  SUCCESS: Clicked using {cand}")
        break
    except Exception as e:
        print(f"  {cand}: {e}")

print("\nDone. Pausing 5 seconds before quit...")
time.sleep(5)
driver.quit()
