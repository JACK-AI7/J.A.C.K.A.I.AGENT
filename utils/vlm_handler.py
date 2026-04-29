import requests
import base64
import os
import json
from core.logger import log_event

class VLMHandler:
    """Interface for local Vision-Language Models (Llava/Llama3.2-Vision) via Ollama."""
    
    def __init__(self, model="llava:latest", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def analyze_image(self, image_path, prompt):
        """Send an image and prompt to the VLM and return the description."""
        if not os.path.exists(image_path):
            return f"VLM Error: Image not found at {image_path}"

        try:
            with open(image_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }

            log_event(f"VLM: Analyzing image {image_path} with prompt: {prompt[:50]}...")
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "No response from VLM.")
        except Exception as e:
            log_event(f"VLM Error: {str(e)}")
            return f"VLM Analysis Failed: {str(e)}"

# Singleton for system-wide access
vlm_handler = VLMHandler()
