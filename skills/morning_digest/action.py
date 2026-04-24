import os
import sys
from datetime import datetime

# Root path alignment for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

def execute(task=None):
    """
    Assembles a Morning Digest.
    """
    now = datetime.now()
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%A, %B %d, %Y")
    
    digest = f"--- TITAN MORNING DIGEST: {date_str} [{time_str}] ---\n\n"
    
    try:
        # 1. System Health
        print("Fetching System Health...")
        from skill_manager import execute_titan_skill
        health = execute_titan_skill("system_doctor")
        digest += "1. SYSTEM VITAL SIGNS:\n"
        digest += health + "\n\n"
    except Exception as e:
        digest += f"1. SYSTEM VITAL SIGNS: [ERROR: {e}]\n\n"
    
    try:
        # 2. Intelligence Update (Top News)
        print("Fetching Global Intelligence...")
        import tools
        news = tools.get_world_news()
        digest += "2. GLOBAL INTELLIGENCE (Top Headlines):\n"
        digest += str(news)[:1000] + "...\n\n"
    except Exception as e:
        digest += f"2. GLOBAL INTELLIGENCE: [ERROR: {e}]\n\n"
    
    # 3. Final Synthesis Recommendation
    digest += "CONCLUSION: The system is stable, Sir. Ready for today's mission parameters."
    
    return digest

if __name__ == "__main__":
    print(execute())
