import subprocess
import os
import uuid
from core.logger import log_event

class DockerExecutor:
    """Safe code execution backend using Docker, inspired by Hermes Agent."""
    
    def __init__(self, image="python:3.10-slim"):
        self.image = image

    def run_python_code(self, code: str):
        """Run Python code inside a temporary Docker container."""
        log_event("DOCKER_EXEC: Initializing isolated container...")
        
        # Save code to a temp file
        temp_file = f"temp_code_{uuid.uuid4()}.py"
        with open(temp_file, "w") as f:
            f.write(code)
            
        try:
            # Run docker command
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{os.getcwd()}/{temp_file}:/app/script.py",
                self.image,
                "python", "/app/script.py"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            output = result.stdout
            error = result.stderr
            
            if result.returncode == 0:
                log_event("DOCKER_EXEC: Execution SUCCESS.")
                return f"Output:\n{output}"
            else:
                log_event(f"DOCKER_EXEC: Execution FAILED: {error}")
                return f"Error:\n{error}\nOutput:\n{output}"
                
        except Exception as e:
            return f"Docker Error: {str(e)}"
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

# Singleton instance
docker_executor = DockerExecutor()

def execute_in_docker(code: str):
    """Tool for JACK to run code in a safe, isolated Docker container."""
    # Check if docker is available
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except:
        return "Docker is not installed or running on this system. Falling back to local execution is recommended, but Docker is preferred for safety."
        
    return docker_executor.run_python_code(code)
