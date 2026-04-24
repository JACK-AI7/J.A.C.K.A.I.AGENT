import os
import sys
import subprocess
import shutil

def check_component(name, command=None, check_file=None, check_module=None):
    print(f"[{name}] Check Initiated...")
    try:
        # 1. Check Python Module
        if check_module:
            try:
                __import__(check_module)
                print(f"  - Status: PASSED (Module '{check_module}' available)")
                return True
            except ImportError as e:
                print(f"  - Status: FAILED (Module '{check_module}' missing: {e})")
                return False

        # 2. Check CLI Command
        if command:
            # First check if the command exists at all to avoid shell errors
            cmd_root = command.split()[0]
            if not shutil.which(cmd_root) and not check_module: 
                # If which fails, it might still be a builtin or internal command, but usually it's a fail on Windows
                pass 
                
            result = subprocess.run(command, capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                output = result.stdout.strip().split('\n')[0][:50]
                print(f"  - Status: PASSED\n  - Data: {output}...")
                return True
            else:
                print(f"  - Status: FAILED ({result.stderr.strip()[:100]})")
                return False

        # 3. Check File Existence
        if check_file:
            # Resolve relative to project root (one level up from utils/)
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_path = os.path.join(root_dir, check_file)
            if os.path.exists(target_path):
                print(f"  - Status: PASSED (Found at {check_file})")
                return True
            else:
                print(f"  - Status: FAILED (Not found at {check_file})")
                return False
    except Exception as e:
        print(f"  - Status: ERROR ({str(e)})")
        return False

def run_health_check():
    print("="*45)
    print(" J.A.C.K. TITAN: GLOBAL HEALTH AUDIT (2026)")
    print("="*45)
    
    all_passed = True
    
    # 1. Brain Health (Ollama)
    if not check_component("Neural Brain (Ollama)", command="ollama list"):
        all_passed = False
    
    # 2. Vision Health (LLAVA/Gemini)
    if not check_component("Visual Sensors (LLAVA)", command="ollama show llava"):
        # Not critical if Gemini is available
        print("  ! Info: Local vision (LLAVA) unavailable. Relying on Cloud Vision.")
    
    # 3. Premium Services Audit
    print("[Neural Network] Auditing Cloud Interface...")
    premium_services = [
        ("Google Gemini", "google.generativeai", "GEMINI_API_KEY"),
        ("ElevenLabs TTS", "elevenlabs", "ELEVENLABS_API_KEY"),
        ("OpenAI Whisper", "openai", "OPENAI_API_KEY"),
        ("Groq AI", "groq", "GROQ_API_KEY")
    ]
    for name, module, env_key in premium_services:
        mod_ok = check_component(f"Service: {name}", check_module=module)
        key_ok = os.getenv(env_key) and "your_" not in os.getenv(env_key)
        if not key_ok:
            print(f"  - KeyStatus: MISSING ({env_key})")
        if not (mod_ok and key_ok):
            print(f"  ! Warning: {name} will operate in LOCAL/FALLBACK mode.")

    # 4. UI Framework (PySide6)
    if not check_component("UI Framework (PySide6)", check_module="PySide6"):
        all_passed = False

    # 4. Automation Health (Playwright)
    if not check_component("Browser Engine (Playwright)", command="python -m playwright --version"):
        all_passed = False
    
    # 5. Computer Control Health (Interpreter)
    if not check_component("System Control (Interpreter)", check_module="interpreter"):
        all_passed = False
    
    # 6. Skill Library Health (Comprehensive Audit)
    skills = [
        "auto_claw", "auto_coder", "camera_skill", "computer_use",
        "datetime_ops", "detection_skill", "email_ops", "file_ops",
        "github_hunter", "httpx", "memory_ops", "multimodal_live_skill",
        "research_titan", "screenshot_ops", "system_doctor", "system_ops",
        "titan_expander", "tool_swarm", "web_ops", "whatsapp_skill",
        "windows_master", "youtube_master"
    ]
    
    print(f"[Skill Library] Commencing verification of {len(skills)} modules...")
    passed_skills = 0
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for s in skills:
        path = os.path.join(root_dir, "skills", s, "action.py")
        if os.path.exists(path):
            passed_skills += 1
        else:
            # Fallback for meta-skills or those without action.py
            if os.path.exists(os.path.join(root_dir, "skills", s, "SKILL.md")):
                passed_skills += 1
            else:
                print(f"  ! Warning: Skill '{s}' missing entry point.")
    
    print(f"  - Skill Sync: {passed_skills}/{len(skills)} modules verified.")
    if passed_skills < len(skills):
        all_passed = False
    
    # 7. Integration Health (Startup & Persistence)
    if not check_component("Silent Launcher", check_file="setup/launch_JACK_silent.vbs"):
        all_passed = False
        
    if not check_component("Startup Batch", check_file="setup/START_JACK.bat"):
        all_passed = False

    print("="*45)
    if all_passed:
        print(" FINAL VERDICT: JACK IS TITAN-READY.")
        print(" ALL SYSTEMS NOMINAL. MISSION START AUTHORIZED.")
    else:
        print(" FINAL VERDICT: SYSTEM DEGRADED.")
        print(" MANUAL INTERVENTION REQUIRED FOR FULL PERFORMANCE.")
    print("="*45)

if __name__ == "__main__":
    run_health_check()
