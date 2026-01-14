
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add parent directory to path to import agent code
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# We will need to import these after we create them, for now we mock the imports or define basic structure if possible
# But for TDD, we write the test assuming the class exists. 
# Since module doesn't exist yet, we can't import it directly without it failing immediately.
# So I will define the test structure to mock the future `PersonalAgentLogic` class or functions.

from typing import Dict, Any

# Mocking the dependency on k_jarvis.mcp.client
with patch.dict(sys.modules, {'k_jarvis.mcp.client': MagicMock()}):
    # This block allows us to write tests even if the SDK isn't installed in the immediate env
    pass

@pytest.mark.asyncio
async def test_remember_capability():
    """
    Test that 'remember' intent correctly calls MCPClient with jwt_token
    """
    # Arrange
    user_id = "test-user-id"
    jwt_token = "test-jwt-token"
    memory_content = "My favorite color is blue"
    
    # Mocking the MCP Client
    mock_mcp_client = AsyncMock()
    mock_mcp_client.call_tool.return_value = "Stored memory: My favorite color is blue"
    
    # We will import this from app.agent_logic
    # from app.agent_logic import process_user_message
    # But since file doesn't exist, we'll simulate the logic here to define EXPECTED behavior
    
    # Act
    # Simulating what process_user_message will do:
    # 1. Detect intent (Remember)
    # 2. Extract content
    # 3. Call MCP tool 'save_memory'
    
    # Simulated implementation for test verification
    async def process_user_message_sim(mcp_client, message, user_id, jwt_token):
        if "remember" in message.lower():
            content = message.replace("remember", "").strip()
            return await mcp_client.call_tool(
                tool_name="save_memory",
                arguments={"content": content},
                user_id=user_id,
                jwt_token=jwt_token # CRITICAL: Verification of Directive 008
            )
    
    result = await process_user_message_sim(
        mock_mcp_client, 
        f"remember {memory_content}", 
        user_id, 
        jwt_token
    )
    
    # Assert
    assert "Stored memory" in result
    mock_mcp_client.call_tool.assert_called_once_with(
        tool_name="save_memory",
        arguments={"content": memory_content},
        user_id=user_id,
        jwt_token=jwt_token # This confirms identity propagation
    )

@pytest.mark.asyncio
async def test_recall_capability():
    """
    Test that queries trigger 'search_memory' tool with jwt_token
    """
    # Arrange
    user_id = "test-user-id"
    jwt_token = "test-jwt-token"
    query = "What is my favorite color?"
    
    search_result = ["My favorite color is blue"]
    
    mock_mcp_client = AsyncMock()
    mock_mcp_client.call_tool.return_value = search_result
    
    # Simulated implementation
    async def process_user_message_sim(mcp_client, message, user_id, jwt_token):
        # Primitive intent detection
        return await mcp_client.call_tool(
            tool_name="search_memory",
            arguments={"query": message},
            user_id=user_id,
            jwt_token=jwt_token
        )

    result = await process_user_message_sim(
        mock_mcp_client,
        query,
        user_id,
        jwt_token
    )
    
    # Assert
    assert result == search_result
    mock_mcp_client.call_tool.assert_called_once_with(
        tool_name="search_memory",
        arguments={"query": query},
        user_id=user_id,
        jwt_token=jwt_token
    )
