import asyncio
import json
import os
import sys
from playwright.async_api import async_playwright

# Root path alignment for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class BrowserOperator:
    """
    OpenJarvis-inspired Browser Operator.
    Uses Playwright to interact with pages using a simplified DOM representation.
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.interactive_elements = {}

    async def start(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            print("Browser Operator: Engine Online.")

    async def navigate(self, url):
        await self.start()
        if not url.startswith("http"):
            url = f"https://{url}"
        await self.page.goto(url)
        return f"Navigated to {url}"

    async def get_clean_dom(self):
        """
        Extracts only interactive elements from the page.
        Inspired by OpenJarvis AXTree implementation.
        """
        await self.start()
        
        # JavaScript to find all interactive elements and return their details
        script = """
        () => {
            const elements = document.querySelectorAll('button, a, input, select, textarea, [role="button"], [role="link"]');
            return Array.from(elements).map((el, index) => {
                const rect = el.getBoundingClientRect();
                return {
                    id: index,
                    tag: el.tagName,
                    role: el.getAttribute('role'),
                    text: el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.value || '',
                    visible: rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).display !== 'none',
                    location: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }
                };
            }).filter(el => el.visible && el.text.trim().length > 0);
        }
        """
        raw_elements = await self.page.evaluate(script)
        self.interactive_elements = {str(el['id']): el for el in raw_elements}
        
        report = "--- ACCESSIBILITY DOM TREE ---\n"
        for eid, el in self.interactive_elements.items():
            report += f"[{eid}] {el['tag']}: \"{el['text'][:50]}\"\n"
        
        return report if raw_elements else "No interactive elements found."

    async def click_id(self, element_id):
        await self.start()
        eid = str(element_id)
        if eid in self.interactive_elements:
            el = self.interactive_elements[eid]
            # Use coordinates for precision click (UFO style)
            await self.page.mouse.click(el['location']['x'], el['location']['y'])
            return f"Clicked element {eid}: {el['text']}"
        return f"Error: Element ID {element_id} not found. Run 'inspect_dom' first."

    async def type_id(self, element_id, text):
        await self.start()
        eid = str(element_id)
        if eid in self.interactive_elements:
            el = self.interactive_elements[eid]
            await self.page.mouse.click(el['location']['x'], el['location']['y'])
            await self.page.keyboard.type(text)
            await self.page.keyboard.press("Enter")
            return f"Typed '{text}' into element {eid}."
        return f"Error: Element ID {element_id} not found."

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.playwright = None
        print("Browser Operator: Engine Offline.")

# Singleton for tool integration
browser_operator = BrowserOperator()

async def execute_operator_task(action, **kwargs):
    """Bridge for sync tool calls."""
    try:
        if action == "navigate":
            return await browser_operator.navigate(kwargs.get("url"))
        elif action == "inspect":
            return await browser_operator.get_clean_dom()
        elif action == "click":
            return await browser_operator.click_id(kwargs.get("id"))
        elif action == "type":
            return await browser_operator.type_id(kwargs.get("id"), kwargs.get("text"))
        elif action == "close":
            await browser_operator.close()
            return "Browser closed."
    except Exception as e:
        return f"Browser Operator Error: {str(e)}"

def sync_browser_operator(action, **kwargs):
    """Sync wrapper."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(execute_operator_task(action, **kwargs))

if __name__ == "__main__":
    # Test script
    print(sync_browser_operator("navigate", url="google.com"))
    print(sync_browser_operator("inspect"))
    print(sync_browser_operator("close"))
