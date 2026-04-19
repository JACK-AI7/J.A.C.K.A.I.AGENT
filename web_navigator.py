import time

# Safe import — Playwright may not be installed yet
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("TITAN Web: Playwright not installed. Run 'python -m playwright install chromium' to enable.")


class WebNavigator:
    """Manages a Playwright-controlled Chromium browser for Jarvis with full DOM access."""
    
    def __init__(self, headless=False):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless
    
    def _ensure_driver(self):
        """Lazy load the Playwright driver."""
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not installed. Run: pip install playwright && python -m playwright install chromium")
        if self.page is None:
            print(f"Launching Playwright Automation Engine (Headless={self.headless})...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.page.set_viewport_size({"width": 1280, "height": 720})
    
    def navigate(self, url):
        self._ensure_driver()
        
        # Smart URL Resolution
        common_sites = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "gmail": "https://mail.google.com",
            "github": "https://github.com",
            "openai": "https://chat.openai.com",
        }
        
        url_lower = url.lower().strip()
        if url_lower in common_sites:
            url = common_sites[url_lower]
        elif "." not in url and not url.startswith("http"):
            url = f"https://www.google.com/search?q={url}"
        elif not url.startswith("http"):
            url = f"https://{url}"
            
        print(f"Navigating to {url}...")
        try:
            self.page.goto(url, wait_until="networkidle", timeout=30000)
            return f"Navigated to {url}"
        except Exception as e:
            return f"Failed to navigate to {url}: {str(e)}"
    
    def click_element(self, text=None, selector=None):
        self._ensure_driver()
        try:
            if text:
                # Use Playwright's robust text locator
                target = self.page.get_by_text(text, exact=False).first
            elif selector:
                target = self.page.locator(selector).first
            else:
                return "No target specified for click."
            
            target.click(timeout=10000)
            return f"Clicked element matching '{text or selector}'"
        except Exception as e:
            return f"Failed to click: {str(e)}"
    
    def fill_input(self, text, selector=None, name=None):
        self._ensure_driver()
        try:
            if selector:
                target = self.page.locator(selector).first
            elif name:
                target = self.page.get_by_placeholder(name).first if "search" in name else self.page.locator(f"[name='{name}']").first
            else:
                return "No target specified for input."
            
            target.fill(text)
            target.press("Enter")
            return f"Filled input with '{text}'"
        except Exception as e:
            # Fallback attempt
            try:
                self.page.keyboard.type(text)
                self.page.keyboard.press("Enter")
                return f"Attempted keyboard typing fallback for '{text}'"
            except:
                return f"Failed to fill input: {str(e)}"

    # --- DOM AUTOMATION TOOLS ---

    def get_dom_elements(self, max_elements=50):
        """Extract interactive DOM elements from the current page."""
        self._ensure_driver()
        try:
            elements = self.page.evaluate('''() => {
                const interactives = Array.from(document.querySelectorAll('button, a, input, select, textarea, [role="button"], [onclick]'));
                return interactives.filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).visibility !== 'hidden';
                }).map((el, idx) => ({
                    index: idx,
                    tag: el.tagName,
                    text: (el.innerText || '').trim().substring(0, 80) || el.getAttribute('aria-label') || el.placeholder || '',
                    id: el.id || '',
                    name: el.name || '',
                    type: el.type || '',
                    href: el.href || '',
                    className: (el.className || '').substring(0, 50),
                    selector: el.id ? '#' + el.id : (el.name ? `[name="${el.name}"]` : '')
                })).slice(0, ''' + str(max_elements) + ''');
            }''')
            
            summary = f"Found {len(elements)} interactive DOM elements:\n"
            for el in elements:
                label = el.get('text') or el.get('id') or el.get('name') or '(no label)'
                summary += f"  [{el['index']}] <{el['tag'].lower()}> {label}"
                if el.get('type'):
                    summary += f" type={el['type']}"
                if el.get('href'):
                    summary += f" href={el['href'][:60]}"
                summary += "\n"
            return summary
        except Exception as e:
            return f"DOM extraction error: {str(e)}"
    
    def click_by_selector(self, selector):
        """Click a DOM element by CSS selector."""
        self._ensure_driver()
        try:
            self.page.click(selector, timeout=10000)
            return f"Clicked element: {selector}"
        except Exception as e:
            return f"Click failed for '{selector}': {str(e)}"
    
    def type_in_selector(self, selector, text):
        """Type text into a DOM element by CSS selector."""
        self._ensure_driver()
        try:
            self.page.fill(selector, text, timeout=10000)
            return f"Typed '{text}' into {selector}"
        except Exception as e:
            return f"Type failed for '{selector}': {str(e)}"

    def get_interaction_map(self):
        """Extract only interactive elements to simplify AI reasoning."""
        return self.get_dom_elements()

    def get_page_summary(self):
        self._ensure_driver()
        try:
            title = self.page.title()
            # Extract main text content
            text = self.page.content()
            # Basic text extraction from HTML
            import re
            clean_text = re.sub('<[^<]+?>', '', text)
            clean_text = ' '.join(clean_text.split())[:2000]
            return f"Page: {title}\nContent Snippet: {clean_text}"
        except Exception as e:
            return f"Failed to get summary: {str(e)}"
    
    def close(self):
        if self.playwright:
            print("Closing Playwright instance...")
            try:
                self.browser.close()
                self.playwright.stop()
            except Exception:
                pass
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            return "Automation Engine closed."
        return "No engine running."

# Singleton for Jarvis
web_navigator = WebNavigator(headless=False)
