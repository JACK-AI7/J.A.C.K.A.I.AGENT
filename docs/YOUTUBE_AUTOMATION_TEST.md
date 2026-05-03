# YOUTUBE AUTOMATION TEST - COMPLETE GUIDE

## 🎯 What This Test Does

Full end-to-end automation test of YouTube:
1. **Open Chrome** and navigate to YouTube
2. **Find and click** the first video thumbnail
3. **Click Subscribe** to the channel
4. **Verify** video is playing

All actions use **1100% human-like** movement, typing, and clicking.

## 🚀 Running the Test

```bash
cd C:\Users\bjasw\Downloads\jarvis-main\jarvis-main
python tests/youtube_automation_test.py
```

### Test Modes

**Mode 1** - Full DesktopAgent + VisualOrchestrator
- Uses humanized mouse/keyboard
- AI vision to find elements
- Realistic clicking with Bezier curves

**Mode 2** - WebNavigator (DOM-based)
- Uses Playwright for direct DOM access
- Faster, more reliable selectors
- Bypasses visual detection

**Mode 3** - Both (comprehensive)

## 📋 Prerequisites

### Required Software:
- ✅ Chrome browser installed
- ✅ Ollama with `llava` model (for vision mode)
- ✅ EasyOCR (for visual mode)
- ✅ Playwright chromium (for web_navigator)

### Install Playwright:
```bash
pip install playwright
python -m playwright install chromium
```

### Pull LLaVA model:
```bash
ollama pull llava
```

## 🧪 Expected Behavior

### Mode 1 (Visual/DesktopAgent)

```
┌─────────────────────────────────────┐
│ YOUTUBE AUTOMATION TEST             │
├─────────────────────────────────────┤
│ [STEP 1] Opening Chrome...          │
│   DesktopAgent: At your command... │
│ [STEP 2] Navigating to YouTube...   │
│   WebNavigator: Navigated to...    │
│ [STEP 3] Finding first video...     │
│   Trying: 'first video thumbnail'  │
│   VisualOrchestrator: Clicked '... │
│ [STEP 4] Subscribing to channel...  │
│   Trying: 'subscribe button'       │
│   ✓ Clicked subscribe              │
│ [STEP 5] Verifying playback...      │
│   ✓ Video appears to be playing    │
└─────────────────────────────────────┘
```

**Live HUD Display:**
```
┌─────────────────────────────────────┐
│ 🤖 AGENT MATRIX                    │
│ ┌─ DesktopAgent ──────────────┐   │
│ │ [ACTIVE] ●                 │   │
│ │ OPEN: chrome → At your...  │   │
│ │ Thinking: typing URL...    │   │
│ └────────────────────────────┘   │
│ ┌─ VisualOrchestrator ───────┐   │
│ │ [ACTIVE] ●                 │   │
│ │ CLICK: first video → OK    │   │
│ │ Thinking: found coordinates│   │
│ └────────────────────────────┘   │
└─────────────────────────────────────┘
```

## 🔍 How It Works

### 1. **Open YouTube**
```python
da.open_application("chrome")  # Human-like launch
time.sleep(2)
da.type_text("https://youtube.com")  # Human typing with typos
da.human.hotkey('ctrl', 'enter')  # Staggered hotkey
```

### 2. **Find First Video**
- **Strategy 1**: DOM selector via web_navigator (`ytd-video-renderer`)
- **Strategy 2**: VisualOrchestrator `smart_click("first video thumbnail")`
- **Strategy 3**: SystemController `visual_locate("video")` → click
- **Strategy 4**: Fallback to center-screen click

### 3. **Subscribe**
- Searches for `"subscribe button"` or `"SUBSCRIBE"`
- Clicks using multiple fallback strategies
- Note: May require login → may fail gracefully

### 4. **Verification**
- Looks for `"pause"` button (indicates playing)
- Checks for time display (`01:23 / 10:45`)
- Reports success/failure

## 🎨 Agent HUD Visualization

As the test runs, HUD shows:

| Agent | Status | Action Displayed |
|-------|--------|------------------|
| DesktopAgent | ACTIVE pulsing | `OPEN: chrome` → `TYPE: https://...` |
| WebNavigator | ACTIVE | `NAVIGATE: youtube.com` |
| VisualOrchestrator | THINKING → ACTIVE | `CLICK: first video thumbnail` |
| SystemController | ACTIVE (if used) | `OCR locate: "subscribe"` |

## 📊 Success Criteria

- ✅ Chrome opens
- ✅ YouTube loads (check title or URL)
- ✅ First video clicked (video player visible)
- ⚠️ Subscribe may fail if not logged in (expected)
- ✅ Video playback verified via UI elements

## 🔧 Troubleshooting

### "WebNavigator not available"
```bash
pip install playwright
python -m playwright install chromium
```

### "Could not find video"
- Ensure YouTube fully loaded (increase `time.sleep()`)
- Check internet connection
- Try again - visual detection can be slow

### "Subscribe button not found"
- Expected if not logged into YouTube
- Login first manually, then run test
- Or ignore - subscription not critical for test

### "EasyOCR/LLaVA errors"
```bash
pip install easyocr torch torchvision
ollama pull llava
```

## 📁 Test Files

- `tests/youtube_automation_test.py` - Main test script
- Can be run standalone or from test suite

## 🎯 Real-World Usage

This test demonstrates JARVIS' ability to:
- Control desktop applications
- Navigate complex web interfaces
- Use AI vision to find UI elements
- Execute multi-step workflows
- Handle errors with graceful fallbacks

You can adapt this pattern for:
- Any website automation
- Form filling
- Data extraction
- Scheduled tasks

---

**Run it**: `python tests/youtube_automation_test.py`
**Watch HUD**: See all agents working in real-time!
**Status**: ✅ Complete and ready
