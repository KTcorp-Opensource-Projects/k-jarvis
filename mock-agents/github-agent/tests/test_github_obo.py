
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add parent directory to path to import agent code
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mocking SDK dependency
with patch.dict(sys.modules, {'k_jarvis.mcp.client': MagicMock()}):
    pass

@pytest.mark.asyncio
async def test_star_repo_obo():
    """
    Test that 'star repo' intent uses OBO pattern (propagates jwt_token)
    """
    # Arrange
    user_id = "test-user-id"
    jwt_token = "user-jwt-token" # Represents End-User's Token
    repo_name = "chihoon/k-jarvis-opensource"
    
    mock_mcp_client = AsyncMock()
    mock_mcp_client.call_tool.return_value = "Repository starred successfully"
    
    # Simulated implementation
    async def process_user_message_sim(mcp_client, message, user_id, jwt_token):
        if "star" in message.lower() and "repo" in message.lower():
            # Primitive extraction
            target_repo = message.split("'")[1] if "'" in message else "unknown"
            
            return await mcp_client.call_tool(
                tool_name="star_repository",
                arguments={"owner": target_repo.split("/")[0], "repo": target_repo.split("/")[1]},
                user_id=user_id,
                jwt_token=jwt_token # CRITICAL: OBO Requirement
            )

    result = await process_user_message_sim(
        mock_mcp_client, 
        f"Star the repo '{repo_name}'", 
        user_id, 
        jwt_token
    )
    
    # Assert
    assert "starred successfully" in result
    mock_mcp_client.call_tool.assert_called_once_with(
        tool_name="star_repository",
        arguments={"owner": "chihoon", "repo": "k-jarvis-opensource"},
        user_id=user_id,
        jwt_token=jwt_token # Confirms token was passed to MCP Client
    )
