import asyncio
import os
import sys
import unittest

# Add root to path
sys.path.append(os.getcwd())

from core.aimp_bridge import AIMPBridge
from memory.persistent_memory import persistent_memory
from core.skill_learner import SkillLearner

class TestHermesIntegration(unittest.TestCase):
    
    def test_aimp_wrapping(self):
        msg = AIMPBridge.wrap_tool_call("test_tool", {"arg1": "val1"})
        self.assertEqual(msg["header"]["type"], "tool_request")
        self.assertEqual(msg["body"]["action"], "test_tool")
        print("AIMP Wrapping: PASSED")

    def test_persistent_memory(self):
        mem_id = persistent_memory.add_memory("JACK is a powerful agent.", "test_memory")
        self.assertIsNotNone(mem_id)
        results = persistent_memory.search("powerful agent")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0]["content"], "JACK is a powerful agent.")
        print("Persistent Memory (FTS5): PASSED")

    def test_skill_learner_init(self):
        # Mock AI handler
        class MockAI:
            def generate(self, prompt): return '{"should_learn": false, "reasoning": "test"}'
        
        learner = SkillLearner(MockAI())
        self.assertIsNotNone(learner)
        print("Skill Learner Initialization: PASSED")

if __name__ == "__main__":
    unittest.main()
