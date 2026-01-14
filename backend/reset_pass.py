
import asyncio
from app.database import get_session_maker
from app.auth.security import get_password_hash
from sqlalchemy import text

async def reset_password():
    print(f"Resetting admin password to 'admin'...")
    new_hash = get_password_hash("admin")
    async with get_session_maker()() as session:
        await session.execute(
            text("UPDATE users SET password_hash = :hash WHERE username = 'admin'"),
            {"hash": new_hash}
        )
        await session.commit()
    print("Password reset complete.")

if __name__ == "__main__":
    asyncio.run(reset_password())
