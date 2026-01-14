import asyncio
import sys
import os

# Ensure /app is in path
sys.path.append("/app")

from app.orchestrator import GlobalHttpClient, orchestrator
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="DEBUG")

async def test_a2a():
    print("\n[TEST] 1. Initializing GlobalHttpClient...")
    await GlobalHttpClient.initialize()
    
    # Target the Sample Agent within the Docker Network
    agent_url = "http://sample-agent:5020"
    message = "echo Internal Architecture Verification"
    
    print(f"\n[TEST] 2. Sending A2A Message to {agent_url}...")
    try:
        # Simulate an A2A call using the Orchestrator's internal method
        # This exercises:
        # - GlobalHttpClient (Singleton)
        # - Tenacity Retry Logic (Implicitly active)
        # - Header Injection (X-MCPHub-User-Id)
        response = await orchestrator._send_to_agent(
            agent_url=agent_url,
            message=message,
            context_id="verify-arch-test-v1",
            user_id="internal-tester",
            kauth_user_id="auth-user-123", # Verify header injection log
            reference_task_ids=["task-1", "task-2"] # Verify A2A standard field
        )
        
        print("\n[TEST] 3. Response Received:")
        print(response)
        
        content = str(response.get("content", ""))
        state = response.get("state")
        
        if state == "completed" and "Architecture Verification" in content:
             print("\n[SUCCESS] A2A Call Verified! GlobalHttpClient is working.")
        else:
             print(f"\n[FAILURE] Unexpected response content: {content}")
             
    except Exception as e:
        print(f"\n[ERROR] Exception during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await GlobalHttpClient.close()

if __name__ == "__main__":
    asyncio.run(test_a2a())
