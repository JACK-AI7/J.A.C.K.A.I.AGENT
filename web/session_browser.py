import os
from playwright.sync_api import sync_playwright

class BrowserSession:
    """Persistent browser session for JACK (keeps logins/cookies alive)."""
    def __init__(self, user_data_dir="./vault/browser_session"):
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)
            
        self.p = sync_playwright().start()
        self.browser = self.p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={'width': 1280, 'height': 720}
        )
        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()

    def open(self, url):
        """Navigate to a URL."""
        self.page.goto(url, wait_until="networkidle")
        return f"Successfully materialized portal to: {url}"

    def click(self, selector):
        """Perform a precision click."""
        self.page.wait_for_selector(selector, timeout=5000)
        self.page.click(selector)
        return f"Interaction SUCCESS: Clicked element matching '{selector}'"

    def type(self, selector, text):
        """Perform a precision type."""
        self.page.wait_for_selector(selector, timeout=5000)
        self.page.fill(selector, text)
        return f"Interaction SUCCESS: Injected neural data into '{selector}'"

    def read(self, selector):
        """Read content from an element."""
        self.page.wait_for_selector(selector, timeout=5000)
        content = self.page.inner_text(selector)
        return content

    def close(self):
        """Safely de-initialize the browser session."""
        self.browser.close()
        self.p.stop()
