import time
import json
import os
from typing import List, Dict, Any, Optional
from config import CONTEXT_SETTINGS, AUTONOMOUS_SETTINGS
from memory_vault import vault


class ConversationManager:
    def __init__(self):
        self.conversation_history = []
        self.history_file = "conversation_history.json"
        self.max_context_length = CONTEXT_SETTINGS["max_context_length"]
        self.max_tokens_per_message = CONTEXT_SETTINGS["max_tokens_per_message"]
        self.enable_context = CONTEXT_SETTINGS["enable_context"]
        self.context_window = CONTEXT_SETTINGS["context_window"]

        # Autonomous settings
        self.max_tool_calls = AUTONOMOUS_SETTINGS["max_tool_calls"]
        self.enable_autonomous = AUTONOMOUS_SETTINGS["enable_autonomous"]
        self.tool_call_timeout = AUTONOMOUS_SETTINGS["tool_call_timeout"]
        self.enable_planning = AUTONOMOUS_SETTINGS["enable_planning"]
        self.max_planning_steps = AUTONOMOUS_SETTINGS["max_planning_steps"]

        # Load history on init
        self.load_history()

    def add_interaction(
        self, user_query: str, assistant_response: str, tool_calls: List[Dict] = None
    ):
        """Add a new interaction to the conversation history."""
        interaction = {
            "timestamp": time.time(),
            "user_query": user_query,
            "assistant_response": assistant_response,
            "tool_calls": tool_calls or [],
        }

        self.conversation_history.append(interaction)

        # Maintain conversation length
        if len(self.conversation_history) > self.max_context_length:
            self.conversation_history.pop(0)

        # Save after adding
        self.save_history()

    def get_context_messages(self) -> List[Dict[str, str]]:
        """Get recent conversation context for AI processing."""
        if not self.enable_context or not self.conversation_history:
            return []

        context_messages = []
        recent_interactions = self.conversation_history[-self.context_window :]

        for interaction in recent_interactions:
            # Truncate messages if too long
            user_query = self._truncate_text(interaction["user_query"])
            assistant_response = self._truncate_text(interaction["assistant_response"])

            context_messages.append({"role": "user", "content": user_query})
            context_messages.append(
                {"role": "assistant", "content": assistant_response}
            )

        # --- LONGER-TERM RAG (Neural Archive) ---
        # Fetch relevant facts from the vector DB to ground the response
        try:
            last_query = recent_interactions[-1]["user_query"]
            relevant_facts = vault.retrieve_relevant_facts(last_query)
            if relevant_facts:
                fact_block = "\n".join([f"- {f}" for f in relevant_facts])
                context_messages.insert(0, {
                    "role": "system", 
                    "content": f"NEURAL ARCHIVE DATA (Relevant Facts):\n{fact_block}\nUse this historical context if relevant to the current mission."
                })
        except Exception as e:
            print(f"Memory Vault Retrieval Error: {e}")

        return context_messages

    def _truncate_text(self, text: str) -> str:
        """Truncate text to fit token limits."""
        if len(text) <= self.max_tokens_per_message:
            return text

        # Simple truncation - in production, you might want to use a proper tokenizer
        return text[: self.max_tokens_per_message] + "..."

    def get_conversation_summary(self) -> str:
        """Get a summary of recent conversation for context."""
        if not self.conversation_history:
            return ""

        recent_interactions = self.conversation_history[-3:]  # Last 3 interactions
        summary_parts = []

        for interaction in recent_interactions:
            summary_parts.append(f"User: {interaction['user_query']}")
            summary_parts.append(f"Assistant: {interaction['assistant_response']}")

        return " | ".join(summary_parts)

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()

    def get_history_length(self) -> int:
        """Get current conversation history length."""
        return len(self.conversation_history)

    def should_use_autonomous_mode(self, query: str) -> bool:
        """Determine if autonomous mode should be used for this query."""
        if not self.enable_autonomous:
            return False

        query_lower = query.lower()
        
        # 1. Check for specific multi-step indicators
        # Handle "first ... then" logic correctly (not as a literal string)
        if "first" in query_lower and "then" in query_lower:
            return True
            
        # 2. Keywords that suggest complex multi-step tasks
        autonomous_keywords = [
            "search and then",
            "after you find",
            "once you",
            "follow these steps",
            "multiple tasks",
        ]

        return any(keyword in query_lower for keyword in autonomous_keywords)

    def create_planning_prompt(self, query: str) -> str:
        """Create a planning prompt for complex tasks."""
        context_summary = self.get_conversation_summary()

        planning_prompt = f"""
        Task: {query}
        
        Recent Context: {context_summary}
        
        Plan the steps needed to complete this task. Consider:
        1. What information do I need to gather?
        2. What tools should I use and in what order?
        3. What actions should I take on the desktop?
        4. How should I present the final result?
        
        Provide a step-by-step plan with specific tool calls and actions.
        """

        return planning_prompt

    def validate_tool_sequence(self, tool_calls: List[Dict]) -> bool:
        """Validate if a sequence of tool calls is reasonable."""
        if len(tool_calls) > self.max_tool_calls:
            return False

        # Add more validation logic here if needed
        return True

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get statistics about conversation and tool usage."""
        total_tool_calls = sum(
            len(interaction.get("tool_calls", []))
            for interaction in self.conversation_history
        )

        return {
            "total_interactions": len(self.conversation_history),
            "total_tool_calls": total_tool_calls,
            "average_tools_per_interaction": total_tool_calls
            / max(len(self.conversation_history), 1),
            "context_enabled": self.enable_context,
            "autonomous_enabled": self.enable_autonomous,
        }

    def save_history(self):
        """Save conversation history to file."""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.conversation_history, f, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")

    def load_history(self):
        """Load conversation history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.conversation_history = json.load(f)
        except Exception as e:
            print(f"Failed to load history: {e}")
            self.conversation_history = []
