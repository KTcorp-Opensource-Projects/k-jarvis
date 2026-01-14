
import os
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from agent_logic import GitHubAgentLogic

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GitHubAgent")

app = FastAPI(title="GitHub Agent")
agent_logic = GitHubAgentLogic()

class MessagePart(BaseModel):
    text: str

class Message(BaseModel):
    role: str
    parts: List[MessagePart]
    messageId: str
    contextId: Optional[str] = None

class A2ARequest(BaseModel):
    jsonrpc: str
    id: str
    method: str
    params: Dict[str, Any]

@app.post("/tasks/send")
async def handle_task(
    request: A2ARequest,
    authorization: Optional[str] = Header(None),
    x_mcp_user_id: Optional[str] = Header(None, alias="X-Mcp-User-Id"),
    x_mcphub_user_id: Optional[str] = Header(None, alias="X-MCPHub-User-Id") 
):
    """
    Handle A2A SendMessage request for GitHub Operations
    """
    try:
        method = request.method
        if method != "SendMessage":
            raise HTTPException(status_code=400, detail="Method not supported")

        params = request.params
        message_obj = params.get("message", {})
        parts = message_obj.get("parts", [])
        
        if not parts:
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "result": {"content": "Empty message received", "state": "done"}
            }
            
        user_message = parts[0].get("text", "")
        user_id = x_mcp_user_id or x_mcphub_user_id
        
        # Extract JWT for OBO
        jwt_token = None
        if authorization and authorization.lower().startswith("bearer "):
            jwt_token = authorization.split(" ")[1]
            
        logger.info(f"Processing GitHub request: '{user_message}' for user: {user_id}")
        
        response_text = await agent_logic.process_user_message(
            user_message,
            user_id=user_id,
            jwt_token=jwt_token
        )
        
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {
                "content": response_text,
                "state": "done",
                "artifacts": []
            }
        }

    except Exception as e:
        logger.error(f"Error handling task: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {"code": -32603, "message": str(e)}
        }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "github-agent"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082) # Port 8082 for GitHub Agent
