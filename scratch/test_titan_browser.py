
import sys
import os
import asyncio

# Add root and core to sys.path
root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(root)
sys.path.append(os.path.join(root, "core"))

async def main():
    try:
        from agents.agent_browser import TitanBrowser
        print("TitanBrowser imported successfully.")
        browser = TitanBrowser()
        print("Running task: Go to youtube.com")
        result = await browser.run_task("Go to youtube.com and tell me if you are there.")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
