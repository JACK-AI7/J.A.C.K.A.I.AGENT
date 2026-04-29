import json

def parse_llm_output(text: str):
    """Strict JSON handler for JACK Production Core."""
    try:
        # Try to extract JSON from potential markdown/clutter
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group()
            
        data = json.loads(text.strip())
        if "type" not in data:
            raise ValueError("Missing type")
        return data
    except Exception:
        return {
            "type": "final",
            "status": "failed",
            "message": "Invalid model response format"
        }
