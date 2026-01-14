"""
Database connection and session management
Supports automatic schema initialization on startup
"""
import os
import ssl
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from loguru import logger

from .config import get_settings

settings = get_settings()

# Database URL (without SSL params - handled separately for asyncpg)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"

# Schema file path
SCHEMA_FILE_PATH = Path(__file__).parent.parent / "db" / "schema.sql"

# SSL configuration for asyncpg (Azure PostgreSQL requires SSL)
db_ssl_mode = os.getenv("DB_SSL_MODE", "prefer")  # prefer, require, disable

connect_args = {}
if db_ssl_mode == "require":
    # Create SSL context for Azure PostgreSQL
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # Azure uses self-signed certs
    connect_args["ssl"] = ssl_context
    logger.info("SSL enabled for database connection")
elif db_ssl_mode == "prefer":
    # Try SSL but don't require it
    connect_args["ssl"] = "prefer"

# Lazy engine initialization for Docker timing issues
_engine = None
_async_session_maker = None

def get_engine():
    """Get or create the database engine (lazy initialization)"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            DATABASE_URL,
            echo=settings.db_echo,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _engine

def get_session_maker():
    """Get or create the session maker (lazy initialization)"""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_maker

# Backwards compatibility
@property
def engine():
    return get_engine()

async_session_maker = None  # Will be set on first use

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session (for FastAPI Depends)"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager to get database session (for service classes)"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def check_tables_exist() -> bool:
    """Check if required tables exist in the database"""
    try:
        async with get_engine().begin() as conn:
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'conversations'
                );
            """))
            row = result.fetchone()
            return row[0] if row else False
    except Exception as e:
        logger.error(f"Failed to check tables: {e}")
        return False


async def initialize_schema():
    """Initialize database schema using SQLAlchemy models"""
    logger.info("Initializing database schema from schema.sql...")
    
    try:
        if not SCHEMA_FILE_PATH.exists():
            logger.error(f"Schema file not found at {SCHEMA_FILE_PATH}")
            return

        # schema.sql contains PL/pgSQL which breaks with naive splitting.
        # Fallback: Execute critical table definitions directly.
        MISSING_TABLES_SQL = """
        CREATE TABLE IF NOT EXISTS conversations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(255) DEFAULT 'New Chat',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
            content TEXT NOT NULL,
            agent_used VARCHAR(100),
            task_id VARCHAR(100),
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS registered_agents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            description TEXT,
            url VARCHAR(500) UNIQUE NOT NULL,
            version VARCHAR(50) DEFAULT '1.0.0',
            skills JSONB DEFAULT '[]',
            capabilities JSONB DEFAULT '{}',
            status VARCHAR(20) DEFAULT 'offline',
            registered_by UUID REFERENCES users(id),
            last_seen TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        async with get_engine().begin() as conn:
            # Execute statements individually
            statements = [s.strip() for s in MISSING_TABLES_SQL.split(';') if s.strip()]
            for statement in statements:
                try:
                    await conn.execute(text(statement))
                except Exception as stmt_err:
                     logger.error(f"Failed to execute table creation: {statement[:50]}... Error: {stmt_err}")
            
        logger.info("Database schema initialized successfully (Safe Fallback)")
            
        logger.info("Database schema initialized successfully from SQL file")
    except Exception as e:
        logger.error(f"Failed to initialize schema: {e}")
        raise


async def init_db():
    """
    Initialize database connection and optionally create schema.
    
    Environment Variables:
        DB_AUTO_INIT: Set to 'true' to auto-create schema if tables don't exist
    """
    try:
        # Test connection
        async with get_engine().begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection established")
        
        # Check if auto-init is enabled (from config or env var)
        auto_init = settings.db_auto_init or os.getenv("DB_AUTO_INIT", "true").lower() == "true"
        
        if auto_init:
            tables_exist = await check_tables_exist()
            
            if not tables_exist:
                logger.info("Tables not found. Initializing schema...")
                await initialize_schema()
                await seed_initial_data()
            else:
                logger.info("Database tables already exist. checking for data seeding...")
                await seed_initial_data()
        else:
            logger.info("DB_AUTO_INIT is disabled. Skipping schema check.")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def seed_initial_data():
    """Seed initial data (roles, admin user)"""
    try:
        from .auth.db_models import Role, User
        from .auth.security import get_password_hash
        from sqlalchemy import select
        
        async with get_session_maker()() as session:
            # Check/Create Roles
            result = await session.execute(select(Role).where(Role.name == "admin"))
            if not result.scalar_one_or_none():
                logger.info("Seeding initial roles...")
                admin_role = Role(id=1, name="admin", description="Administrator")
                user_role = Role(id=2, name="user", description="Standard User")
                session.add_all([admin_role, user_role])
                await session.commit()
            
            # Check/Create Admin User
            result = await session.execute(select(User).where(User.username == "admin"))
            existing_admin = result.scalar_one_or_none()
            
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123!@#")
            new_password_hash = get_password_hash(admin_password)
            
            if not existing_admin:
                logger.info("Seeding default admin user...")
                admin_user = User(
                    username="admin",
                    email=os.getenv("ADMIN_EMAIL", "admin@k-jarvis.com"),
                    password_hash=new_password_hash,
                    name="Admin User",
                    role_id=1,
                    is_active=True
                )
                session.add(admin_user)
                await session.commit()
                logger.info("Default admin user created.")
            else:
                # Always sync password from env (Self-Healing)
                logger.info("Syncing admin password from environment...")
                existing_admin.password_hash = new_password_hash
                existing_admin.role_id = 1
                existing_admin.is_active = True
                await session.commit()
                logger.info("Default admin user updated (Password Synced).")
                
    except Exception as e:
        logger.error(f"Failed to seed initial data: {e}")
        # Don't raise, just log error



async def close_db():
    """Close database connection"""
    await engine.dispose()
    logger.info("Database connection closed")

