import asyncio
import httpx
import time
import json

URL = "http://localhost:4001/api/chat/message"  # Direct Orchestrator API
# Using direct Chat API which internally calls Orchestrator.process_message -> A2A Agent

async def send_request(i):
    async with httpx.AsyncClient() as client:
        start = time.time()
        payload = {
            "message": f"echo Concurrent Request {i}",
            "conversation_id": f"concurrency-test-{i}",
            "stream": false
        }
        # Note: The Orchestrator's /api/chat/message endpoint expects ChatRequest
        # We need to target the Orchestrator Port 4001 directly
        
        try:
            response = await client.post(URL, json=payload, timeout=30.0)
            elapsed = time.time() - start
            return i, response.status_code, elapsed
        except Exception as e:
            return i, "ERROR", str(e)

async def main():
    print(f"Starting concurrency test against {URL}...")
    tasks = [send_request(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    for i, status, elapsed in results:
        print(f"Req {i}: Status={status}, Time={elapsed:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
