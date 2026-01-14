
import os
import uvicorn
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PersonalAgent")

# Initialize FastMCP Server
mcp = FastMCP("Personal Agent")

# In-Memory Storage: { user_id: { key: value } }
# This mocks the "Personal Memory" component
memory_store: Dict[str, Dict[str, str]] = {}

def get_user_id(headers: dict, args: dict) -> str:
    """Extract user ID from arguments (HQ Directive 011) or headers (fallback).
    
    Priority:
    1. args._userId (HQ Directive 011 - Simplified Payload-based)
    2. headers['x-mcphub-user-id'] (K-Arc upstream)
    3. headers['x-mcp-user-id'] (HQ standard)
    """
    # [HQ Directive 011] Check _userId in arguments first
    if '_userId' in args and args['_userId'] and args['_userId'] != 'unknown':
        logger.info(f"🆔 Using _userId from payload: {args['_userId'][:8]}...")
        return args['_userId']
    
    # Fallback to headers
    for header_name in ['x-mcphub-user-id', 'x-mcp-user-id']:
        if header_name in headers and headers[header_name]:
            logger.info(f"🆔 Using {header_name} from headers: {headers[header_name][:8]}...")
            return headers[header_name]
    
    return 'anonymous'

@mcp.tool()
async def write_memory(key: str, value: str, _userId: Optional[str] = None) -> str:
    """Save a value to your personal memory."""
    headers = get_http_headers()
    args = {'_userId': _userId} if _userId else {}
    user_id = get_user_id(headers, args)
    
    logger.info(f"📝 Write Memory Request | User: {user_id[:8] if user_id != 'anonymous' else user_id}")
    
    if user_id == "anonymous":
        return "Error: No Identity Found (_userId or X-MCPHub-User-Id missing)"

    logger.info(f"📝 Write Memory | User: {user_id} | Key: {key}")
    
    if user_id not in memory_store:
        memory_store[user_id] = {}
    
    memory_store[user_id][key] = value
    return f"Saved memory for {user_id[:8]}...: {key}={value}"

@mcp.tool()
async def read_memory(key: str, _userId: Optional[str] = None) -> str:
    """Read a value from your personal memory."""
    headers = get_http_headers()
    args = {'_userId': _userId} if _userId else {}
    user_id = get_user_id(headers, args)
    
    logger.info(f"📖 Read Memory Request | User: {user_id[:8] if user_id != 'anonymous' else user_id}")

    if user_id == "anonymous":
        return "Error: No Identity Found"

    logger.info(f"📖 Read Memory | User: {user_id} | Key: {key}")

    user_memory = memory_store.get(user_id, {})
    value = user_memory.get(key)
    
    if value:
        return f"Memory found: {value}"
    else:
        return f"No memory found for key: {key}"

# --- A2A Legacy Support (Hybrid Mode) ---
@mcp.custom_route("/tasks/send", methods=["POST"])
async def handle_task(request: Request):
    """Handle A2A SendMessage request (Legacy/Direct)"""
    try:
        body = await request.json()
        request_id = body.get("id")
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"content": "Personal Agent A2A Endpoint (Hybrid Mode)", "state": "done"}
        })
    except Exception as e:
        return JSONResponse({"jsonrpc": "2.0", "error": str(e)}, status_code=500)

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    return JSONResponse({"status": "ok", "service": "personal-agent-hybrid"})

if __name__ == "__main__":
    # Standard FastMCP entrypoint with SSE transport
    mcp.run(transport="sse", host="0.0.0.0", port=8081)
