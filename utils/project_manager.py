import os
import shutil
import datetime

class ProjectManager:
    """Gives JACK the ability to inspect and improve his own source code."""
    
    def __init__(self):
        self.root_dir = os.getcwd()
        self.backup_dir = os.path.join(self.root_dir, "backups")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        # Security Whitelist: Only these files can be modified by the AI
        self.allowed_files = [
            "hud_manager.py",
            "jack_ai_agent.py",
            "ai_handler.py",
            "tools.py",
            "project_manager.py",
            "config.py",
            "conversation_manager.py"
        ]

    def list_project_structure(self):
        """List all core project files for analysis."""
        files = []
        for root, _, filenames in os.walk(self.root_dir):
            if "__pycache__" in root or "venv" in root or ".git" in root or "backups" in root:
                continue
            for f in filenames:
                if f.endswith(".py") or f.endswith(".json") or f == ".env.example":
                    files.append(os.path.relpath(os.path.join(root, f), self.root_dir))
        return "\n".join(files)

    def read_source_code(self, file_path):
        """Read a source file for improvement analysis."""
        abs_path = os.path.abspath(os.path.join(self.root_dir, file_path))
        if not abs_path.startswith(self.root_dir):
            return "Security Error: Access denied to outside files."
        
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Read Error: {str(e)}"

    def apply_improvement(self, file_path, new_content):
        """Apply a code improvement with automatic backup and security filtering."""
        rel_path = os.path.relpath(os.path.abspath(os.path.join(self.root_dir, file_path)), self.root_dir)
        
        # Policy Check: Only allow whitelisted files
        if rel_path not in self.allowed_files:
            return f"Security Error: AI is not authorized to modify '{rel_path}'. Only Agent Core files are allowed."

        abs_path = os.path.join(self.root_dir, rel_path)

        try:
            # Create backup
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"{os.path.basename(file_path)}_{timestamp}.bak")
            shutil.copy(abs_path, backup_path)
            
            # Apply improvement
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return f"Self-Improvement Applied to {file_path}. Backup created at {os.path.relpath(backup_path, self.root_dir)}"
        except Exception as e:
            return f"Improvement Error: {str(e)}"

    def verify_integrity(self):
        """Run a basic self-check to ensure syntax is valid across project."""
        import compileall
        result = compileall.compile_dir(self.root_dir, quiet=1)
        return "System Integrity Verified." if result else "Integrity Check Failed: Syntax Errors Detected."

# Singleton for JACK
project_manager = ProjectManager()
