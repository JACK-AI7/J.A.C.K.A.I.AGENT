#!/usr/bin/env python
"""
Test PrecisionDOMAgent: Open YouTube (using installed Chrome) and play first video.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'core'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'agents'))

from agents.precision_dom_agent import PrecisionDOMAgent, youtube_play_first_video

def main():
    print("="*70)
    print("PrecisionDOMAgent - YouTube Automation Test")
    print("="*70)
    print()
    print("[INFO] Running in automated mode: Launch Chrome -> YouTube -> Play first video")
    
    # Auto-confirm; comment out if manual needed
    # confirm = input("Proceed? (y/n): ").strip().lower()
    # if confirm != 'y':
    #     print("Aborted.")
    #     return
    
    print("\n[START] Running mission...")
    result = youtube_play_first_video()
    print()
    print(result)
    print()
    print("="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
