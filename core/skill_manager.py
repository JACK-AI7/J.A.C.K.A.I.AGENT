import os
import sys
import importlib.util
import json
import logging

class SkillManager:
    """The engine that discovers and executes modular JACK Skills."""
    
    def __init__(self, skills_dir="skills"):
        self.skills_dir = skills_dir
        self.skills = {}
        self.load_skills()

    def load_skills(self):
        """Discover skills by scanning for SKILL.md and action.py."""
        print("Skill Manager: Discovering new TITAN abilities...")
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir)
            
        # Clear existing to allow clean reload
        self.skills = {}
            
        for root, dirs, files in os.walk(self.skills_dir):
            # Only look in immediate subdirectories of skills_dir for standard skills
            if root == self.skills_dir:
                for item in dirs:
                    item_path = os.path.join(root, item)
                    manifest_path = os.path.join(item_path, "SKILL.md")
                    script_path = os.path.join(item_path, "action.py")
                    
                    if os.path.exists(manifest_path) and os.path.exists(script_path):
                        try:
                            # Parse SKILL.md for description
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest_content = f.read()
                            
                            description = manifest_content.split('\n')[0].replace('#', '').strip()
                            
                            self.skills[item] = {
                                "name": item,
                                "description": description or item,
                                "full_manifest": manifest_content,
                                "path": script_path
                            }
                            print(f"Skill Loaded: {item}")
                        except Exception as e:
                            print(f"Warning: Failed to load skill '{item}': {e}")

    def refresh_skills(self):
        """Force a scan of the skills directory."""
        self.load_skills()
        return f"Neural Refresh Complete. {len(self.skills)} abilities online."

    def run_skill(self, skill_name, task=None):
        """Execute a specialized skill dynamically."""
        if skill_name not in self.skills:
            # Try to reload in case a new skill was dropped in
            self.load_skills()
            if skill_name not in self.skills:
                # Fuzzy matching attempt? (Optional: for later)
                return f"Skill Error: '{skill_name}' not found in the library."
        
        skill = self.skills[skill_name]
        print(f"Executing TITAN Skill: {skill_name}")
        
        try:
            # Force reload of the module if it was already imported to ensure we use fresh code
            # (Important for development and hot-loading)
            if skill_name in sys.modules:
                del sys.modules[skill_name]
                
                
            spec = importlib.util.spec_from_file_location(skill_name, skill["path"])
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "execute"):
                return module.execute(task)
            else:
                return f"Skill Error: '{skill_name}' is missing an 'execute' function."
        except Exception as e:
            logging.error(f"Skill Execution Failed: {e}")
            return f"Skill Execution Failed: {str(e)}"

# Singleton Skill Manager
skill_manager = SkillManager()

def execute_titan_skill(skill_name, task=None):
    """Bridge for the toolset."""
    return skill_manager.run_skill(skill_name, task)

def refresh_titan_skills():
    """Tool bridge for refreshing the library."""
    return skill_manager.refresh_skills()
