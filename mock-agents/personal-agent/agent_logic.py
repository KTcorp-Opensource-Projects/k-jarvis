
from typing import Dict, Any, Optional
import os
from k_jarvis.mcp.client import MCPClient

class PersonalAgentLogic:
    def __init__(self):
        # In a real scenario, base_url might come from env
        # K-Arc MCP Hub URL
        self.mcp_hub_url = os.getenv("MCP_HUB_URL", "http://k-arc:3000/mcp")
        self.api_key = os.getenv("MCP_HUB_TOKEN", "mock-token") 
        self.client = MCPClient(base_url=self.mcp_hub_url, api_key=self.api_key)

    async def process_user_message(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        jwt_token: Optional[str] = None
    ) -> str:
        """
        Process user message and interact with Personal Memory via MCP
        Directive 008: Must propagate jwt_token
        """
        
        # 1. Simple Intent Detection
        if message.lower().startswith("remember"):
            # Intent: Save Memory
            content = message[8:].strip() # remove "remember "
            if not content:
                return "What should I remember?"
            
            try:
                result = await self.client.call_tool(
                    tool_name="save_memory",
                    arguments={"content": content},
                    user_id=user_id,
                    jwt_token=jwt_token # Identity Propagation
                )
                return f"I have remembered that: {content}"
            except Exception as e:
                return f"Failed to save memory: {str(e)}"
                
        else:
            # Intent: Recall / Search
            try:
                # Semantic search via mcp-personal-memory
                results = await self.client.call_tool(
                    tool_name="search_memory",
                    arguments={"query": message},
                    user_id=user_id,
                    jwt_token=jwt_token # Identity Propagation
                )
                
                if not results:
                    return "I don't recall anything about that."
                
                return f"Here implies what I found: {results}"
                
            except Exception as e:
                return f"Failed to search memory: {str(e)}"
