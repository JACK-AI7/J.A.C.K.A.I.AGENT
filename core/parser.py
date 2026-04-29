import json
import re
import os
import datetime

def parse_llm_output(text: str):
    """Robust JSON handler for JACK Production Core. Extracts JSON even from messy AI output."""
    if not text:
        return {"type": "final", "status": "failed", "message": "Empty response from AI"}

    data = None
    
    # 1. Try Direct Parse
    try:
        data = json.loads(text.strip())
    except:
        # 2. Robust Extraction Logic
        matches = list(re.finditer(r'\{|\}', text))
        for i in range(len(matches)):
            if matches[i].group() == '{':
                for j in range(len(matches) - 1, i, -1):
                    if matches[j].group() == '}':
                        candidate = text[matches[i].start():matches[j].end()]
                        try:
                            candidate_data = json.loads(candidate)
                            if isinstance(candidate_data, dict):
                                data = candidate_data
                                break
                        except:
                            continue
                if data: break

    # 3. Process parsed data
    if isinstance(data, dict):
        if "type" not in data:
            # Default to "final" if it looks like a message
            if any(k in data for k in ["message", "response", "answer", "result"]):
                data["type"] = "final"
                if "status" not in data: data["status"] = "success"
            elif "name" in data and ("args" in data or "task" in data):
                data["type"] = "tool"
            else:
                # Last resort: treat as final if it has ANY content
                data["type"] = "final"
                if "status" not in data: data["status"] = "success"
        return data

    # 4. Fallback: If it's just plain text, treat as final message
    if len(text.split()) < 50 and "{" not in text:
        return {
            "type": "final",
            "status": "success",
            "message": text.strip()
        }

    # 5. Logging failure for debugging
    try:
        if not os.path.exists("logs"):
            os.makedirs("logs")
        with open("logs/parse_errors.log", "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"--- PARSE ERROR AT {timestamp} ---\n")
            f.write(f"RAW INPUT:\n{text}\n")
            f.write("-" * 40 + "\n\n")
    except:
        pass

    return {
        "type": "final",
        "status": "failed",
        "message": "Invalid model response format"
    }
