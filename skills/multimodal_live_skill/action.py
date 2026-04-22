import ollama
import base64
import os
from config import VISION_SETTINGS

def execute(task=None):
    """
    Processes an image through local LLaVA.
    Task should contain the path to the image and the query.
    Format: 'image_path: [path] | query: [query]'
    """
    if not task:
        return "Multimodal Error: No task or image provided."
    
    try:
        # Simple parser for the format
        parts = task.split("|")
        image_path = ""
        query = ""
        
        for part in parts:
            if "image_path:" in part:
                image_path = part.replace("image_path:", "").strip()
            if "query:" in part:
                query = part.replace("query:", "").strip()
        
        if not image_path:
            # Fallback: assume the whole string is a path
            image_path = task.strip()
            query = "What do you see in this image?"
            
        if not os.path.exists(image_path):
            return f"Multimodal Error: Image not found at {image_path}"
        
        print(f"Moltbot Visual Core: Analyzing {os.path.basename(image_path)}...")
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        response = ollama.generate(
            model=VISION_SETTINGS.get("deep_vision_model", "llava:latest"),
            prompt=query,
            images=[image_data]
        )
        
        return response.get('response', "Visual analysis yielded no results.")
        
    except Exception as e:
        return f"Multimodal Visual Error: {str(e)}"
