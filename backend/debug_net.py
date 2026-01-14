
import os
import asyncio
import httpx
import socket

async def main():
    print(f"--- Environment Check ---")
    kauth_url = os.getenv("KAUTH_URL")
    print(f"KAUTH_URL: '{kauth_url}'")
    
    print(f"\n--- DNS Resolution Check (k-auth) ---")
    try:
        ip = socket.gethostbyname("k-auth")
        print(f"Resolved k-auth to: {ip}")
    except Exception as e:
        print(f"Failed to resolve k-auth: {e}")

    print(f"\n--- HTTPX Check ({kauth_url}) ---")
    if not kauth_url:
        print("Skipping HTTPX check because KAUTH_URL is not set.")
        return

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{kauth_url}/health", timeout=5.0)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"HTTPX Request Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
