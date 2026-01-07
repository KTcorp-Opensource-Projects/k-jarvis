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
                    AND table_name = 'users'
                );
            """))
            row = result.fetchone()
            return row[0] if row else False
    except Exception as e:
        logger.error(f"Failed to check tables: {e}")
        return False


async def initialize_schema():
    """Initialize database schema from schema.sql file"""
    if not SCHEMA_FILE_PATH.exists():
        logger.error(f"Schema file not found: {SCHEMA_FILE_PATH}")
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_FILE_PATH}")
    
    logger.info(f"Initializing database schema from {SCHEMA_FILE_PATH}")
    
    # Read schema file
    schema_sql = SCHEMA_FILE_PATH.read_text(encoding='utf-8')
    
    # Split by semicolon and execute each statement
    # (asyncpg doesn't support multiple statements in one execute)
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
    
    async with get_engine().begin() as conn:
        for i, statement in enumerate(statements):
            if statement and not statement.startswith('--'):
                try:
                    await conn.execute(text(statement))
                except Exception as e:
                    # Ignore "already exists" errors
                    if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                        logger.warning(f"Statement {i+1} warning: {e}")
    
    logger.info("Database schema initialized successfully")


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
            else:
                logger.info("Database tables already exist")
        else:
            logger.info("DB_AUTO_INIT is disabled. Skipping schema check.")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """Close database connection"""
    await engine.dispose()
    logger.info("Database connection closed")

