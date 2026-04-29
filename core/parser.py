import json
import re
import os
import datetime

def parse_llm_output(text: str):
    """Robust JSON handler for JACK Production Core. Extracts JSON even from messy AI output."""
    if not text:
        return {"type": "final", "status": "failed", "message": "Empty response from AI"}

    # 1. Try Direct Parse
    try:
        return json.loads(text.strip())
    except:
        pass

    # 2. Robust Extraction Logic
    # Find all { and } positions
    matches = list(re.finditer(r'\{|\}', text))
    
    # Try pairs of braces from outside in to find a valid JSON object with a "type" field
    for i in range(len(matches)):
        if matches[i].group() == '{':
            for j in range(len(matches) - 1, i, -1):
                if matches[j].group() == '}':
                    candidate = text[matches[i].start():matches[j].end()]
                    try:
                        data = json.loads(candidate)
                        if isinstance(data, dict) and "type" in data:
                            return data
                    except:
                        continue

    # 3. Logging failure for debugging
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
