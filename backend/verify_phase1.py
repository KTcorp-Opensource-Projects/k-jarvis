import asyncio
import os
import sys
from loguru import logger

# Ensure k_jarvis module is found (if running directly)
# This is handled by PYTHONPATH in the execution command, but adding runtime check is good
try:
    from k_jarvis.mcp.client import MCPClient
except ImportError:
    print("Error: k_jarvis SDK not found. Make sure PYTHONPATH is set correctly.")
    sys.exit(1)

async def verify_phase1():
    print("=== Phase 1: Real Agent Integration Verification ===")
    
    # 1. Load API Key
    # Try multiple locations
    possible_paths = [
        "arc_api_key.txt",
        "../../arc_api_key.txt", 
        "../../../arc_api_key.txt",
        "/Users/jungchihoon/chihoon/kt-opensource-project-jarvis/arc_api_key.txt"
    ]
    
    api_key_path = None
    for path in possible_paths:
        if os.path.exists(path):
            api_key_path = path
            break
            
        # Try relative to this script
        rel_path = os.path.join(os.path.dirname(__file__), path)
        if os.path.exists(rel_path):
            api_key_path = rel_path
            break
    
    if not api_key_path:
        logger.error("❌ API Key file (arc_api_key.txt) not found.")
        logger.info("Please ensure Phase 0 verification was run and arc_api_key.txt exists in the project root.")
        sys.exit(1)
        
    with open(api_key_path, "r") as f:
        api_key = f.read().strip()
        
    logger.info(f"✅ Loaded API Key from {api_key_path}: {api_key[:10]}...")
    
    # 2. Initialize Client
    # K-Arc local backend is at localhost:3000
    # SDK expects base_url to point to /mcp for JSON-RPC
    # Use 127.0.0.1 to avoid IPv6 resolution issues with httpx on macOS
    base_url = "http://127.0.0.1:3000/mcp"
    logger.info(f"🔌 Connecting to K-Arc at {base_url}...")
    
    client = MCPClient(
        base_url=base_url,
        api_key=api_key,
        timeout=10.0
    )
    
    try:
        # 3. List Tools
        logger.info("📋 Listing tools...")
        tools = await client.list_tools()
        
        if not tools:
            logger.error("❌ No tools returned from K-Arc.")
            sys.exit(1)
            
        logger.info(f"✅ Found {len(tools)} tools.")
        
        echo_tool = next((t for t in tools if t['name'] == 'echo'), None)
        if not echo_tool:
            logger.error("❌ 'echo' tool not found in list.")
            logger.info(f"Available tools: {[t['name'] for t in tools]}")
            sys.exit(1)
            
        logger.info("✅ 'echo' tool confirmed available.")
        
        # 4. Execute Tool
        message = "Phase 1 Python Verification Success"
        logger.info(f"🚀 Executing 'echo' tool with message: '{message}'...")
        
        result = await client.call_tool("echo", {"message": message})
        
        logger.info(f"📥 Result: {result}")
        
        if result:
            logger.info("✅ Tool execution successful.")
            print("\n✨ Verification PASSED: K-Jarvis SDK successfully communicated with K-Arc! ✨")
        else:
            logger.error("❌ Tool execution returned empty result.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(verify_phase1())
