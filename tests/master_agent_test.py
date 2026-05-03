#!/usr/bin/env python
"""Full demonstration of MasterDesktopAgent capabilities."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.master_desktop_agent import MasterDesktopAgent
import time

def full_demo():
    print("\n" + "="*70)
    print("MASTER DESKTOP AGENT - FULL CAPABILITY DEMO")
    print("Shows: screen view, mouse, keyboard, scroll, native UIA & DOM")
    print("="*70)
    
    agent = MasterDesktopAgent()
    
    # === SCREEN VIEWING ===
    print("\n--- 1. SCREEN VIEWING (screenshot + OCR) ---")
    analysis = agent.analyze_screen()
    print(analysis[:600] + "..." if len(analysis)>600 else analysis)
    
    # Show that we can view the top window title via UIA
    print("\n--- 2. NATIVE WINDOW DETECTION (UIA) ---")
    active = agent.get_active_window()
    if active:
        print(f"Active window: '{active.window_text()}'")
        # Dump first level UI tree
        children = active.descendants()
        print(f"  UI elements in active window: {len(children)}")
        interesting = [c for c in children[:30] if c.element_info.name]
        for el in interesting[:10]:
            print(f"    [{el.element_info.control_type}] {el.element_info.name}")
    else:
        print("No active window found")
    
    # === SCROLL TEST (will do in browser later) ===
    print("\n--- 3. SCROLL TEST ---")
    # Open browser first to have something scrollable
    print("  Opening browser to scroll...")
    agent.open_browser_session("https://www.youtube.com")
    time.sleep(3)
    # Scroll down a bit using humanized scroll
    scroll_res = agent.scroll(direction='down', amount=5)
    print(f"  {scroll_res}")
    time.sleep(1)
    
    # === MOUSE CONTROL ===
    print("\n--- 4. MOUSE MOVEMENT TEST ---")
    # Move to search box (known location roughly) using smooth curve
    agent.move_mouse(960, 150, humanized=True)
    print("  Moved mouse to (960,150) with humanized curve")
    time.sleep(0.5)
    
    # === KEYBOARD TYPING ===
    print("\n--- 5. KEYBOARD TYPING TEST ---")
    type_res = agent.type_text("Hello from MasterAgent! Testing typing with humanized delays and occasional typos that auto-correct.")
    print(f"  {type_res}")
    
    # === FULL YOUTUBE WORKFLOW ===
    print("\n--- 6. YOUTUBE SEARCH & PLAY (Logged-in Chrome) ---")
    agent._page.keyboard.press("Control+K")  # focus search via shortcut
    time.sleep(0.5)
    result = agent.youtube_search_play("munna bhaai gaming")
    
    print("\nWorkflow steps:")
    for i, step in enumerate(result['steps'], 1):
        print(f"  {i}. {step}")
    print(f"\nOutcome: {'SUCCESS - video playing' if result['success'] else 'FAIL'}")
    
    # === FINAL STATUS ===
    print("\n--- 7. AGENT STATUS FOR HUD ---")
    status = agent.get_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
    
    # Cleanup
    agent.close_all()
    print("\nBrowser closed. Demo complete.")
    
    return result['success']

if __name__ == "__main__":
    ok = full_demo()
    print("\n" + "="*70)
    print("FINAL RESULT:", "ALL SYSTEMS OPERATIONAL" if ok else "SOME ISSUES DETECTED")
    print("="*70)
    sys.exit(0 if ok else 1)

