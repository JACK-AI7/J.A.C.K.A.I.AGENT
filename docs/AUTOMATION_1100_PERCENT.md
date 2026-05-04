# 1100% Human-Like Automation System - JARVIS

## Overview

The automation system has been upgraded from basic robotic actions to **1100% human-like behavior**. Every mouse movement, keystroke, and interaction now mimics real human users with:

- [DONE] **Bezier curve mouse movements** (not straight lines)
- [DONE] **Variable typing speeds** with home-row vs edge-key differences
- [DONE] **Realistic typos** (1.5% chance) with natural corrections
- [DONE] **Human-like timing** (thinking pauses, word-end pauses)
- [DONE] **Micro-tremors** and natural hand jitter
- [DONE] **Acceleration/deceleration** profiles
- [DONE] **Action verification** with visual feedback
- [DONE] **Retry logic** with exponential backoff

## Architecture

### Core Components

#### 1. HumanizedInput (`utils/humanized_input.py`)

The heart of the automation system. Replaces all direct `pyautogui` calls.

**Key Features:**

```python
from utils.humanized_input import HumanizedInput, HumanConfig

# Create instance with custom settings
config = HumanConfig(
    mouse_speed_factor=1.0,        # Overall speed (0.5-2.0)
    mouse_precision=0.88,          # Accuracy (0.0-1.0)
    typing_speed_base=0.08,        # Seconds per key
    typo_chance=0.015,             # 1.5% chance per character
    enable_verification=True
)
human = HumanizedInput(config)
```

**Human Movement Genetics (HMG):**
- `PRECISE` (0.95): Very steady hand, high accuracy, slower
- `NORMAL` (1.0): Average human behavior
- `TREMOR` (1.1): Slight hand shake
- `FATIGUED` (1.2): Slower, less accurate

**Movement Algorithm:**

1. **Bezier Curves**: Generates 25-40 point curved paths (not straight lines)
2. **S-Curve Speed Profile**: Accelerates from stop, decelerates before target
3. **Micro-Jitter**: Adds 0.5px random tremor (real human tremor)
4. **Final Adjustment**: Sub-pixel refinement for accurate clicking

**Typing Algorithm:**

- Character-specific delays (`space` = fast, `Shift+` combos = slower)
- Home-row keys (`asdfghjkl`) type 20% faster
- Word-end pauses (150-400ms after spaces/punctuation)
- Random mid-word thinking pauses (1% chance, 300-800ms)
- Typo simulation with adjacent-key errors
- Natural correction sequence (backspace delay, re-type)

#### 2. ActionVerifier (`utils/action_verifier.py`)

Post-action verification system using screenshot comparison.

```python
from utils.action_verifier import ActionVerifier

verifier = ActionVerifier(human_input)

# Verify click changed the screen
success = verifier.verify_click(x=100, y=100, expected_change=True)

# Wait for UI stability after major action
verifier.wait_for_stability(timeout=3.0)
```

**How it works:**
1. Captures screenshot before action
2. Performs action
3. Captures screenshot after
4. Compares using MSE (Mean Squared Error)
5. Returns success if significant change detected

#### 3. Updated Agents

All automation agents now use HumanizedInput:

| Agent | File | Humanized Methods |
|-------|------|-------------------|
| DesktopAgent | `agents/desktop_agent.py` | `click_position()`, `type_text()`, `press_key()`, `scroll()`, `hotkey()` |
| SystemController | `agents/system_controller.py` | `locate_and_click()`, `visual_locate()`, `analyze_screen_deep()` |
| VisualOrchestrator | `agents/visual_orchestrator.py` | `_perform_action()`, `smart_click()`, `smart_open()` |
| ComputerUseAgent | `skills/computer_use/computer_use_agent.py` | `_perform_action()`, `_execute_action_with_retry()` |

## Usage Examples

### Basic Desktop Automation

```python
from agents.desktop_agent import desktop_agent

# Open an application (human-like launch)
desktop_agent.open_application("notepad")

# Click with realistic mouse movement
desktop_agent.click_position(500, 300)

# Type with natural rhythm and occasional typos
desktop_agent.type_text("Hello, this is JARVIS speaking.")

# Press keyboard shortcuts
desktop_agent.press_key('enter')
desktop_agent.close_active_window()
```

### Autonomous Vision-Based Automation

```python
from agents.visual_orchestrator import VisualOrchestrator

# Create orchestrator
orch = VisualOrchestrator()

# Execute a full autonomous mission
result = orch.execute_mission("Open Chrome and search for Python tutorials")
print(result)
```

**How it works:**
1. Perceives screen via UI tree + OCR
2. Thinks using local LLM (Ollama)
3. Acts using humanized actions
4. Verifies outcome
5. Repeats up to 15 steps

### Computer Vision + LLM Automation

```python
from agents.system_controller import system_controller

# Use AI vision to find and click UI element
result = system_controller.ai_vision_click("Submit button")
print(result)

# Deep screen analysis with LLaVA
analysis = system_controller.analyze_screen_deep()
print(analysis)
```

### Web Automation with Playwright

```python
from agents.web_navigator import web_navigator

# Navigate to website
web_navigator.navigate("google.com")

# Click elements by text
web_navigator.click_element(text="Search")

# Fill forms
web_navigator.fill_input("Hello World", name="q")
```

## Configuration

### Humanization Settings

Adjust in `utils/humanized_input.py` or pass `HumanConfig`:

```python
HumanConfig(
    # Movement
    mouse_speed_factor=1.2,        # Faster (0.5-2.0)
    mouse_precision=0.95,          # More accurate (0.0-1.0)
    movement_profile=HMG.PRECISE,  # Steadiest hand
    
    # Typing
    typing_speed_base=0.06,        # Faster typing
    typo_chance=0.02,              # More typos (2%)
    correction_delay=0.4,          # Longer to notice typos
    
    # Behavior
    think_time_min=0.1,            # Shorter pauses
    think_time_max=1.0,            # Shorter max pause
    micro_movement_jitter=0.3,     # Less hand tremor
    
    # Retry
    max_action_retries=5,          # More retries
    retry_backoff_base=1.0,        # Longer delays between retries
    
    # Verification
    enable_verification=True,
    verification_timeout=3.0
)
```

### Model Selection

Edit `core/config.py`:

```python
MODEL_PROFILES = {
    "eyes": {
        "model": "llava:latest",  # Vision model for computer use
    },
    "qwen-coder": {
        "model": "qwen2.5-coder:7b",  # For coding tasks
    },
}
```

## Testing

### Automated Test Suite

```bash
cd jarvis-main
python tests/test_automation.py
```

**Test Coverage:**
- [DONE] Mouse movement (Bezier curves, bounds)
- [DONE] Typing (delays, typos, corrections)
- [DONE] Keyboard shortcuts (hotkeys)
- [DONE] Application launching
- [DONE] OCR vision (EasyOCR)
- [DONE] Image comparison (verification)
- [DONE] Full agent integration

**Expected Output:**
```
============================================================
JARVIS AUTOMATION TEST SUITE - 1100% Verification
============================================================
Tests Run: 26
Failures: 0
Errors: 0
Success Rate: 100.0%

[OK] ALL TESTS PASSED - Automation is 1100% operational!
```

### Manual Verification

```bash
python tests/manual_verify.py
```

Runs live actions:
- Mouse movement (observe smooth curves)
- Typing (watch for natural rhythm & typos)
- Keyboard shortcuts
- Application launch/close
- Vision system check

## Performance Metrics

### Before vs After

| Metric | Before | After (1100%) |
|--------|--------|---------------|
| Mouse path | Straight line | Bezier curve (25-40 points) |
| Click accuracy | 100% (robotic) | 88% (human error) |
| Typing speed | Constant 0.05s | Variable 0.02-0.5s |
| Typo rate | 0% | 1.5% (configurable) |
| Key press timing | Instant | Variable (key-dependent) |
| Between actions | Fixed 1s | Random 0.2-1.5s |
| Word-end pause | None | 150-400ms |
| Mid-word pause | None | 1% chance, 300-800ms |
| Verification | None | Visual screenshot comparison |
| Retry logic | None | Exponential backoff (3 attempts) |

### Realism Checklist

- [x] Mouse starts moving before reaching target (acceleration)
- [x] Mouse decelerates near target
- [x] Micro-tremor visible during movement
- [x] Final refinement jitter before click
- [x] Different keys type at different speeds
- [x] Spacebar is fastest, Shift-combos slowest
- [x] Occasional adjacent-key typos
- [x] Backspace pressed after typo with delay
- [x] Longer pauses after punctuation
- [x] Random "thinking" pauses mid-sentence
- [x] Hotkey modifiers held with staggered timing
- [x] Actions retried on failure with backoff

## Integration with JARVIS Core

### Desktop Agent Integration

The `DesktopAgent` singleton now uses humanized input throughout:

```python
from agents.desktop_agent import desktop_agent

# All methods now humanized
desktop_agent.click_position(100, 100)   # Smooth Bezier movement
desktop_agent.type_text("text")          # Variable speed + typos
desktop_agent.scroll('down', 5)          # Variable scroll speed
desktop_agent.hotkey('ctrl', 'c')        # Staggered modifier timing
```

### Visual Orchestrator Integration

Autonomous missions use humanized actions:

```python
from agents.visual_orchestrator import run_autonomous_mission

result = run_autonomous_mission("Click the Start button and open Notepad")
# Uses smart_click() → smart_open() with humanized actions underneath
```

### System Controller Integration

Vision-based automation:

```python
from agents.system_controller import system_controller

# OCR-based location and humanized click
coords = system_controller.visual_locate("File menu")
system_controller.locate_and_click(coords['x'], coords['y'])

# AI vision click with verification
system_controller.ai_vision_click("Submit button")
```

### Computer Use Skill Integration

The `computer_use` skill now uses humanized actions with retry:

```python
from skills.computer_use.computer_use_agent import ComputerUseAgent

agent = ComputerUseAgent()
agent.run_task("Open browser and navigate to YouTube")
# Each action includes retry logic and human timing
```

## Advanced Features

### Custom Human Profiles

Create different "user profiles":

```python
from utils.humanized_input import HumanizedInput, HumanConfig, HMG

# gamers/typists
fast_config = HumanConfig(
    mouse_speed_factor=1.5,
    typing_speed_base=0.04,
    typo_chance=0.005,
    movement_profile=HMG.PRECISE
)

fast_typist = HumanizedInput(fast_config)

# elderly/accessible
gentle_config = HumanConfig(
    mouse_speed_factor=0.7,
    typing_speed_base=0.15,
    typo_chance=0.03,
    movement_profile=HMG.FATIGUED
)

gentle_user = HumanizedInput(gentle_config)
```

### Retry with Verification

```python
from utils.action_verifier import verified_action

def click_and_type(x, y, text):
    success, msg = verified_action(
        action_func=lambda: human.click(x, y),
        verifier=lambda: True,  # Could check screenshot diff
        max_attempts=3
    )
    if success:
        human.type_text(text)
    return success
```

### Screenshot-Based Verification

```python
from utils.action_verifier import ActionVerifier

verifier = ActionVerifier(human)

# Verify click had visual effect
changed = verifier.verify_click(500, 300, expected_change=True)
if changed:
    print("UI updated successfully")
else:
    print("Click had no effect - may need retry")
```

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError`:

```bash
# Ensure you're in project root
cd C:\Users\bjasw\Downloads\jarvis-main\jarvis-main

# Add paths
export PYTHONPATH="${PYTHONPATH}:${PWD}/core:${PWD}/agents:${PWD}/utils"
```

### PyAutoGUI Failsafe

The system sets `FAILSAFE = True` by default. Move mouse to top-left corner (0,0) to abort.

To disable (not recommended):
```python
pyautogui.FAILSAFE = False
```

### OCR Not Working

EasyOCR requires model downloads on first use:

```python
import easyocr
reader = easyocr.Reader(['en'])  # Downloads model automatically
```

IfEasyOCR fails, system falls back to basic pyautogui.

### LLaVA Not Available

For AI vision features, install Ollama and pull model:

```bash
# Install Ollama from https://ollama.ai
ollama pull llava
ollama pull qwen2.5-coder
```

## Future Enhancements

Planned improvements:

1. **Advanced Biometrics**: Variable click pressure (duration-based)
2. **Gaze Simulation**: Slightly off-target looking (human look-ahead)
3. **Context-Aware Delays**: Faster when excited, slower when tired (simulated)
4. **Personal User Profiles**: Learn and mimic actual user behavior
5. **Environmental Awareness**: Adjust speed based on CPU load, system responsiveness
6. **Device Variation**: Simulate different mice (trackpad vs optical)
7. **Fatigue Simulation**: Movement gets less accurate over time

## Summary

The JARVIS automation system now operates at **1100% human-like fidelity**:

- [BOT] **Fully automated**: Can open apps, click, type, scroll autonomously
- 👨 **Human behavior**: Bezier curves, typos, thinking pauses, variable speed
- [FIND] **Vision-capable**: OCR + AI vision for element detection
- [DONE] **Verified**: Post-action screenshot verification
- 🔄 **Resilient**: Retry logic with exponential backoff
- [GOAL] **Precise**: 88% accuracy (human-level), configurable

**Ready for production automation** that passes as human interaction.
