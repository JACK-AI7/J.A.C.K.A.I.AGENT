import os
import sys
import subprocess
import shutil

def check_component(name, command=None, check_file=None):
    print(f"[{name}] Check Initiated...")
    try:
        if command:
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                print(f"  - Status: PASSED\n  - Data: {result.stdout.strip().split('\\n')[0][:50]}...")
                return True
            else:
                print(f"  - Status: FAILED ({result.stderr.strip()})")
                return False
        if check_file:
            if os.path.exists(check_file):
                print(f"  - Status: PASSED (Found at {check_file})")
                return True
            else:
                print(f"  - Status: FAILED (Not found)")
                return False
    except Exception as e:
        print(f"  - Status: ERROR ({str(e)})")
        return False

def run_health_check():
    print("="*40)
    print(" JACK TITAN: GLOBAL HEALTH AUDIT (2026)")
    print("="*40)
    
    all_passed = True
    
    # 1. Brain Health (Ollama)
    if not check_component("Neural Brain (Ollama)", command="ollama list"):
        all_passed = False
    
    # 2. Vision Health (LLAVA)
    if not check_component("Visual Sensors (LLAVA)", command="ollama show llava"):
        all_passed = False
    
    # 3. Automation Health (Playwright)
    if not check_component("Browser Engine (Playwright)", command="python -m playwright --version"):
        all_passed = False
    
    # 4. Computer Control Health (Interpreter)
    if not check_component("System Control (Interpreter)", command="interpreter --version"):
        all_passed = False
    
    # 5. Skill Library Health
    skills = [
        "youtube_master", "research_titan", "system_doctor", 
        "auto_coder", "tool_swarm", "github_hunter", 
        "windows_master", "auto_claw", "computer_use",
        "titan_expander"
    ]
    passed_skills = 0
    for s in skills:
        path = os.path.join("skills", s, "action.py")
        if os.path.exists(path): passed_skills += 1
    
    print(f"[Skill Library] {passed_skills}/{len(skills)} specialized modules synced.")
    if passed_skills < len(skills):
        all_passed = False
    
    # 6. Integration Health
    if not check_component("Silent Launcher", check_file="launch_JACK_silent.vbs"):
        all_passed = False
    
    print("="*40)
    if all_passed:
        print(" FINAL VERDICT: JACK IS TITAN-READY.")
    else:
        print(" FINAL VERDICT: SYSTEM DEGRADED. MANUAL INTERVENTION REQUIRED.")
    print("="*40)

if __name__ == "__main__":
    run_health_check()
