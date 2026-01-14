
import asyncio
from app.database import get_session_maker
from app.auth.security import verify_password, get_password_hash
from app.auth.db_models import User
from sqlalchemy import select
import os

async def check_admin_password():
    print(f"Checking admin password...")
    env_password = os.getenv("ADMIN_PASSWORD", "admin123!@#")
    print(f"Env Password: {env_password}")
    
    async with get_session_maker()() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        
        if user:
            print(f"User found: {user.username}")
            print(f"Stored Hash: {user.password_hash}")
            
            is_valid = verify_password(env_password, user.password_hash)
            print(f"Is valid against env password? {is_valid}")
            
            is_valid_default = verify_password("admin123!@#", user.password_hash)
            print(f"Is valid against 'admin123!@#'? {is_valid_default}")
            
            # Re-hash env password to compare
            new_hash = get_password_hash(env_password)
            print(f"New Hash of env password: {new_hash}")
        else:
            print("User 'admin' not found.")

if __name__ == "__main__":
    asyncio.run(check_admin_password())
