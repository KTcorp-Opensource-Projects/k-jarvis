
from typing import Dict, Any, Optional
import os
import logging
from k_jarvis.mcp.client import MCPClient

logger = logging.getLogger("GitHubAgent")

class GitHubAgentLogic:
    def __init__(self):
        # K-Arc MCP Hub URL
        self.mcp_hub_url = os.getenv("MCP_HUB_URL", "http://k-arc-backend:3000/mcp")
        self.api_key = os.getenv("MCP_HUB_TOKEN", "mock-token") 
        self.client = MCPClient(base_url=self.mcp_hub_url, api_key=self.api_key)

    async def process_user_message(
        self, 
        message: str, 
        user_id: Optional[str] = None,
        jwt_token: Optional[str] = None
    ) -> str:
        """
        Process user message and interact with GitHub via MCP
        Directive 008/Active: Must propagate jwt_token (OBO)
        """
        msg_lower = message.lower()
        
        # Intent: Star Repository
        if "star" in msg_lower and "repo" in msg_lower:
            # Simple extraction: assumes 'owner/repo' format in quotes or just present
            # Example: "Star the repo 'chihoon/k-jarvis-opensource'"
            try:
                if "'" in message:
                    repo_full = message.split("'")[1]
                elif '"' in message:
                    repo_full = message.split('"')[1]
                else:
                    # Fallback: try to find pattern owner/repo words
                    words = message.split()
                    repo_full = next((w for w in words if "/" in w), None)
                
                if not repo_full or "/" not in repo_full:
                    return "Please specify the repository as 'owner/repo'."

                owner, repo = repo_full.split("/")
                
                logger.info(f"Attempting to star repo: {owner}/{repo} (User: {user_id})")
                
                # MCP Call with OBO Token
                result = await self.client.call_tool(
                    tool_name="star_repository",
                    arguments={"owner": owner, "repo": repo},
                    user_id=user_id,
                    jwt_token=jwt_token # Identity Propagation (OBO)
                )
                
                return f"Successfully starred repository {owner}/{repo}! (Result: {result})"
                
            except Exception as e:
                logger.error(f"Failed to star repo: {e}")
                return f"Failed to star repository: {str(e)}"
                
        else:
            return "I can help you manage GitHub repositories. Try 'Star the repo owner/name'."
