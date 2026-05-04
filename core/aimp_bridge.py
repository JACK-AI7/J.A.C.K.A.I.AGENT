import uuid
import time
from typing import Dict, Any, Optional

class AIMPMessage:
    """A standard AIMP-compliant message wrapper."""
    def __init__(self, sender: str, recipient: str, message_type: str, payload: Dict[str, Any]):
        self.message_id = str(uuid.uuid4())
        self.timestamp = int(time.time() * 1000)
        self.sender = sender
        self.recipient = recipient
        self.type = message_type
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": {
                "message_id": self.message_id,
                "timestamp": self.timestamp,
                "sender": self.sender,
                "recipient": self.recipient,
                "type": self.type,
                "version": "1.0"
            },
            "body": self.payload
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        header = data.get("header", {})
        body = data.get("body", {})
        msg = cls(
            sender=header.get("sender"),
            recipient=header.get("recipient"),
            message_type=header.get("type"),
            payload=body
        )
        msg.message_id = header.get("message_id", msg.message_id)
        msg.timestamp = header.get("timestamp", msg.timestamp)
        return msg

class AIMPBridge:
    """Standardizes communication between JACK and other agents/tools."""
    
    @staticmethod
    def wrap_tool_call(tool_name: str, args: Dict[str, Any], sender: str = "JACK") -> Dict[str, Any]:
        """Wrap a tool call in AIMP format."""
        payload = {
            "action": tool_name,
            "parameters": args
        }
        return AIMPMessage(sender, tool_name, "tool_request", payload).to_dict()

    @staticmethod
    def wrap_tool_result(tool_name: str, result: Any, sender: str = "SYSTEM") -> Dict[str, Any]:
        """Wrap a tool result in AIMP format."""
        payload = {
            "action": tool_name,
            "result": result
        }
        return AIMPMessage(sender, "JACK", "tool_response", payload).to_dict()

    @staticmethod
    def wrap_chat(text: str, sender: str, recipient: str = "USER") -> Dict[str, Any]:
        """Wrap a chat message in AIMP format."""
        payload = {
            "text": text
        }
        return AIMPMessage(sender, recipient, "chat_message", payload).to_dict()
