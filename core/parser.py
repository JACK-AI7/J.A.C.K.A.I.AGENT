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
        if not data:
            # Pre-process text to fix common pseudo-JSON issues
            # Fix single quotes
            processed_text = re.sub(r"\'(\w+)\'\s*:", r'"\1":', text) # keys
            processed_text = re.sub(r":\s*\'(.*?)\'", r': "\1"', processed_text) # values
            
            matches = list(re.finditer(r'\{|\}', processed_text))
            for i in range(len(matches)):
                if matches[i].group() == '{':
                    for j in range(len(matches) - 1, i, -1):
                        if matches[j].group() == '}':
                            candidate = processed_text[matches[i].start():matches[j].end()]
                            try:
                                # Final cleanup for common mistakes
                                candidate = candidate.replace("'", '"')
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

    # 4. Fallback: If it's just plain text or failed to parse JSON, treat as final message
    # We strip common JSON characters to see if there's any text left
    clean_text = re.sub(r'[\{\}\[\]\"\'\:]', '', text).strip()
    
    if clean_text or len(text) < 500:
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
