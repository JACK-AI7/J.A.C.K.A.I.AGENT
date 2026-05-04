import os
import json
import logging
from typing import List, Dict, Any
from core.logger import log_event

class SkillLearner:
    """The self-evolution engine that converts successful missions into reusable skills."""
    
    def __init__(self, ai_handler, skills_dir="skills"):
        self.ai = ai_handler
        self.skills_dir = skills_dir

    async def reflect_on_mission(self, task: str, trace: List[Dict[str, Any]]):
        """Analyze a completed mission and decide if it warrants a new skill."""
        log_event(f"Reflection: Analyzing mission success for task: {task}")
        
        # Format trace for LLM reflection
        trace_summary = "\n".join([
            f"Step {i+1}: {step.get('type')} - {step.get('name', step.get('action'))} "
            f"Result: {str(step.get('result'))[:100]}..."
            for i, step in enumerate(trace) if step.get('type') in ['tool_execution', 'action']
        ])
        
        prompt = f"""
        Analyze the following successful mission trace and decide if it represents a repeatable workflow that should be automated as a "Skill".
        
        Task: {task}
        Trace:
        {trace_summary}
        
        If this is a common task that would benefit from being a single tool, respond with a JSON object:
        {{
            "should_learn": true,
            "skill_name": "short_snake_case_name",
            "skill_description": "Clear description of what this skill does",
            "reasoning": "Why this is a good skill"
        }}
        Otherwise:
        {{
            "should_learn": false,
            "reasoning": "Explain why not"
        }}
        """
        
        try:
            # We use a direct call to the AI handler for reflection
            response = self.ai.generate([{"role": "user", "content": prompt}])
            # Parse response (assuming JSON)
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                if decision.get("should_learn"):
                    log_event(f"Self-Improvement: Learning new skill '{decision['skill_name']}'")
                    await self._generate_skill(decision, task, trace)
                else:
                    log_event(f"Reflection complete: No new skill needed. {decision.get('reasoning')}")
        except Exception as e:
            log_event(f"Reflection Error: {e}")

    async def _generate_skill(self, decision: Dict[str, Any], task: str, trace: List[Dict[str, Any]]):
        """Generate the Python code and manifest for the new skill."""
        name = decision["skill_name"]
        description = decision["skill_description"]
        
        prompt = f"""
        Create a standalone Python script for a new JACK Skill named '{name}'.
        Description: {description}
        
        The script MUST have an `execute(task)` function.
        It should use standard libraries or existing JACK tools if possible.
        
        Reference Mission: {task}
        Steps taken: {json.dumps(trace, indent=2)}
        
        Respond ONLY with the Python code for action.py. Do not include markdown formatting.
        """
        
        try:
            code = self.ai.generate([{"role": "user", "content": prompt}])
            # Clean up code if LLM added backticks
            code = code.strip()
            if code.startswith("```python"):
                code = code[9:]
            if code.endswith("```"):
                code = code[:-3]
            code = code.strip()
            
            # Create skill directory
            skill_path = os.path.join(self.skills_dir, name)
            os.makedirs(skill_path, exist_ok=True)
            
            # Save action.py
            with open(os.path.join(skill_path, "action.py"), "w", encoding="utf-8") as f:
                f.write(code)
                
            # Save SKILL.md
            with open(os.path.join(skill_path, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(f"# {description}\n\nGenerated autonomously from mission: {task}")
                
            log_event(f"SKILL ACQUIRED: {name} is now online.")
            
            # Refresh Skill Manager
            from core.skill_manager import refresh_titan_skills
            refresh_titan_skills()
            
        except Exception as e:
            log_event(f"Skill Generation Failed: {e}")
