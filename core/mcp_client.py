import asyncio
import json
import httpx
from typing import List, Dict, Any
from core.logger import log_event

class MCPClient:
    """Client for connecting to external Model Context Protocol (MCP) servers."""
    
    def __init__(self):
        self.servers = [] # List of {url, tools}

    async def register_server(self, url: str):
        """Register a new MCP server and discover its tools."""
        log_event(f"MCP: Discovering tools from {url}")
        try:
            async with httpx.AsyncClient() as client:
                # Standard MCP discovery endpoint (hypothetical/simplified)
                response = await client.get(f"{url}/mcp/tools", timeout=5.0)
                if response.status_code == 200:
                    tools = response.json().get("tools", [])
                    self.servers.append({"url": url, "tools": tools})
                    log_event(f"MCP: Registered {len(tools)} tools from {url}")
                    return True
        except Exception as e:
            log_event(f"MCP Registration Error ({url}): {e}")
        return False

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Return all tools discovered from all MCP servers."""
        all_tools = []
        for server in self.servers:
            all_tools.extend(server["tools"])
        return all_tools

    async def execute_tool(self, server_url: str, tool_name: str, args: Dict[str, Any]):
        """Execute a tool on a specific MCP server."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{server_url}/mcp/execute",
                    json={"tool": tool_name, "arguments": args},
                    timeout=30.0
                )
                return response.json()
        except Exception as e:
            return {"error": f"MCP Execution Failed: {str(e)}"}

# Singleton instance
mcp_client = MCPClient()
