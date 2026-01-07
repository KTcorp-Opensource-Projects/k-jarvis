"""
Agent Catalog Service - Database Connection
PostgreSQL async connection management using asyncpg
"""
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
import asyncpg
from loguru import logger


class DatabaseManager:
    """
    Async PostgreSQL database manager using asyncpg
    """
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._dsn = os.getenv(
            "DATABASE_URL",
            "postgresql://mcphub:mcphub@mcphub-postgres-local:5432/agent_catalog"
        )
    
    async def connect(self):
        """Create connection pool"""
        try:
            self._pool = await asyncpg.create_pool(
                self._dsn,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            logger.info(f"Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def disconnect(self):
        """Close connection pool"""
        if self._pool:
            await self._pool.close()
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def connection(self):
        """Get a connection from the pool"""
        if not self._pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self._pool.acquire() as conn:
            yield conn
    
    # =========================================================================
    # Agent Card CRUD Operations
    # =========================================================================
    
    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent card"""
        import uuid as uuid_module
        
        # Convert string ID to UUID
        agent_id = agent_data.get('id')
        if isinstance(agent_id, str):
            agent_uuid = uuid_module.UUID(agent_id)
        else:
            agent_uuid = agent_id or uuid_module.uuid4()
        
        async with self.connection() as conn:
            row = await conn.fetchrow("""
                INSERT INTO agent_cards (
                    id, name, description, url, version, protocol_version,
                    skills, capabilities, default_input_modes, default_output_modes,
                    provider, security_schemes, security, preferred_transport,
                    additional_interfaces, extensions, status, last_seen
                ) VALUES (
                    $1::uuid, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10,
                    $11, $12, $13, $14,
                    $15, $16, $17, $18
                )
                RETURNING *
            """,
                agent_uuid,
                agent_data.get('name'),
                agent_data.get('description'),
                agent_data.get('url'),
                agent_data.get('version', '1.0.0'),
                agent_data.get('protocol_version', '0.3.0'),
                json.dumps(agent_data.get('skills', [])),
                json.dumps(agent_data.get('capabilities', {})),
                json.dumps(agent_data.get('default_input_modes', ['text/plain'])),
                json.dumps(agent_data.get('default_output_modes', ['text/plain'])),
                json.dumps(agent_data.get('provider')) if agent_data.get('provider') else None,
                json.dumps(agent_data.get('security_schemes')) if agent_data.get('security_schemes') else None,
                json.dumps(agent_data.get('security')) if agent_data.get('security') else None,
                agent_data.get('preferred_transport', 'JSONRPC'),
                json.dumps(agent_data.get('additional_interfaces', [])),
                json.dumps(agent_data.get('extensions', {})),
                agent_data.get('status', 'online'),
                agent_data.get('last_seen', datetime.utcnow())
            )
            return self._row_to_dict(row)
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        import uuid as uuid_module
        
        if isinstance(agent_id, str):
            agent_uuid = uuid_module.UUID(agent_id)
        else:
            agent_uuid = agent_id
        
        async with self.connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agent_cards WHERE id = $1::uuid",
                agent_uuid
            )
            return self._row_to_dict(row) if row else None
    
    async def get_agent_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get agent by URL"""
        async with self.connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agent_cards WHERE url = $1",
                url
            )
            return self._row_to_dict(row) if row else None
    
    async def get_agent_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get agent by name (case-insensitive)"""
        async with self.connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM agent_cards WHERE LOWER(name) = LOWER($1)",
                name
            )
            return self._row_to_dict(row) if row else None
    
    async def list_agents(self, include_offline: bool = False) -> List[Dict[str, Any]]:
        """List all agents"""
        async with self.connection() as conn:
            if include_offline:
                rows = await conn.fetch(
                    "SELECT * FROM agent_cards ORDER BY created_at DESC"
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM agent_cards WHERE status = 'online' ORDER BY created_at DESC"
                )
            return [self._row_to_dict(row) for row in rows]
    
    async def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an agent card"""
        import uuid as uuid_module
        
        if isinstance(agent_id, str):
            agent_uuid = uuid_module.UUID(agent_id)
        else:
            agent_uuid = agent_id
        
        async with self.connection() as conn:
            row = await conn.fetchrow("""
                UPDATE agent_cards SET
                    name = COALESCE($2, name),
                    description = COALESCE($3, description),
                    version = COALESCE($4, version),
                    skills = COALESCE($5, skills),
                    capabilities = COALESCE($6, capabilities),
                    extensions = COALESCE($7, extensions),
                    status = COALESCE($8, status),
                    last_seen = COALESCE($9, last_seen)
                WHERE id = $1::uuid
                RETURNING *
            """,
                agent_uuid,
                agent_data.get('name'),
                agent_data.get('description'),
                agent_data.get('version'),
                json.dumps(agent_data.get('skills')) if agent_data.get('skills') else None,
                json.dumps(agent_data.get('capabilities')) if agent_data.get('capabilities') else None,
                json.dumps(agent_data.get('extensions')) if agent_data.get('extensions') else None,
                agent_data.get('status'),
                agent_data.get('last_seen')
            )
            return self._row_to_dict(row) if row else None
    
    async def update_agent_status(
        self, 
        agent_id: str, 
        status: str, 
        last_seen: Optional[datetime] = None
    ) -> bool:
        """Update agent status"""
        import uuid as uuid_module
        
        # Convert string to UUID
        if isinstance(agent_id, str):
            agent_uuid = uuid_module.UUID(agent_id)
        else:
            agent_uuid = agent_id
        
        async with self.connection() as conn:
            result = await conn.execute("""
                UPDATE agent_cards 
                SET status = $2::varchar, 
                    last_seen = COALESCE($3, last_seen),
                    last_health_check = NOW(),
                    health_check_failures = CASE WHEN $2::varchar = 'online' THEN 0 ELSE health_check_failures + 1 END
                WHERE id = $1::uuid
            """,
                agent_uuid,
                status,
                last_seen
            )
            return result == "UPDATE 1"
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        import uuid as uuid_module
        
        if isinstance(agent_id, str):
            agent_uuid = uuid_module.UUID(agent_id)
        else:
            agent_uuid = agent_id
        
        async with self.connection() as conn:
            result = await conn.execute(
                "DELETE FROM agent_cards WHERE id = $1::uuid",
                agent_uuid
            )
            return result == "DELETE 1"
    
    async def search_agents(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skill: Optional[str] = None,
        domain: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search agents by various criteria"""
        conditions = ["1=1"]
        params = []
        param_idx = 1
        
        if query:
            conditions.append(f"(LOWER(name) LIKE LOWER(${param_idx}) OR LOWER(description) LIKE LOWER(${param_idx}))")
            params.append(f"%{query}%")
            param_idx += 1
        
        if tags:
            # Search in skills JSONB for tags
            conditions.append(f"EXISTS (SELECT 1 FROM jsonb_array_elements(skills) AS s WHERE s->'tags' ?| ${param_idx})")
            params.append(tags)
            param_idx += 1
        
        if skill:
            conditions.append(f"EXISTS (SELECT 1 FROM jsonb_array_elements(skills) AS s WHERE LOWER(s->>'name') LIKE LOWER(${param_idx}))")
            params.append(f"%{skill}%")
            param_idx += 1
        
        if domain:
            conditions.append(f"extensions->'routing'->>'domain' = ${param_idx}")
            params.append(domain)
            param_idx += 1
        
        sql = f"SELECT * FROM agent_cards WHERE {' AND '.join(conditions)} ORDER BY created_at DESC"
        
        async with self.connection() as conn:
            rows = await conn.fetch(sql, *params)
            return [self._row_to_dict(row) for row in rows]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get catalog statistics"""
        async with self.connection() as conn:
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_agents,
                    COUNT(*) FILTER (WHERE status = 'online') as online_agents,
                    COUNT(*) FILTER (WHERE status = 'offline') as offline_agents,
                    COUNT(*) FILTER (WHERE status = 'unknown') as unknown_agents,
                    SUM(jsonb_array_length(skills)) as total_skills
                FROM agent_cards
            """)
            
            domains = await conn.fetch("""
                SELECT 
                    COALESCE(extensions->'routing'->>'domain', 'general') as domain,
                    COUNT(*) as count
                FROM agent_cards
                GROUP BY extensions->'routing'->>'domain'
            """)
            
            return {
                "total_agents": stats['total_agents'] or 0,
                "online_agents": stats['online_agents'] or 0,
                "offline_agents": stats['offline_agents'] or 0,
                "unknown_agents": stats['unknown_agents'] or 0,
                "total_skills": stats['total_skills'] or 0,
                "agents_by_domain": {row['domain']: row['count'] for row in domains}
            }
    
    # =========================================================================
    # Health Check History
    # =========================================================================
    
    async def record_health_check(
        self,
        agent_id: str,
        status: str,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Record a health check result"""
        import uuid as uuid_module
        
        # Convert string to UUID if needed
        if isinstance(agent_id, str):
            agent_uuid = uuid_module.UUID(agent_id)
        else:
            agent_uuid = agent_id
        
        async with self.connection() as conn:
            await conn.execute("""
                INSERT INTO health_check_history (agent_id, status, response_time_ms, error_message)
                VALUES ($1::uuid, $2, $3, $4)
            """,
                agent_uuid,
                status,
                response_time_ms,
                error_message
            )
    
    async def get_health_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get health check history for all or specific agent"""
        import uuid as uuid_module
        
        async with self.connection() as conn:
            if agent_id:
                if isinstance(agent_id, str):
                    agent_uuid = uuid_module.UUID(agent_id)
                else:
                    agent_uuid = agent_id
                
                rows = await conn.fetch("""
                    SELECT h.*, a.name as agent_name, a.url as agent_url
                    FROM health_check_history h
                    JOIN agent_cards a ON h.agent_id = a.id
                    WHERE h.agent_id = $1::uuid
                    ORDER BY h.checked_at DESC
                    LIMIT $2
                """, agent_uuid, limit)
            else:
                rows = await conn.fetch("""
                    SELECT h.*, a.name as agent_name, a.url as agent_url
                    FROM health_check_history h
                    JOIN agent_cards a ON h.agent_id = a.id
                    ORDER BY h.checked_at DESC
                    LIMIT $1
                """, limit)
            
            return [self._health_row_to_dict(row) for row in rows]
    
    async def get_agent_health_summary(self) -> List[Dict[str, Any]]:
        """Get health summary for all agents (dashboard view)"""
        async with self.connection() as conn:
            rows = await conn.fetch("""
                SELECT 
                    a.id,
                    a.name,
                    a.url,
                    a.status,
                    a.last_seen,
                    a.last_health_check,
                    a.health_check_failures,
                    (
                        SELECT AVG(response_time_ms)
                        FROM health_check_history h
                        WHERE h.agent_id = a.id 
                        AND h.checked_at > NOW() - INTERVAL '1 hour'
                        AND h.response_time_ms IS NOT NULL
                    ) as avg_response_time_1h,
                    (
                        SELECT COUNT(*) FILTER (WHERE status = 'online')::float / 
                               NULLIF(COUNT(*), 0) * 100
                        FROM health_check_history h
                        WHERE h.agent_id = a.id
                        AND h.checked_at > NOW() - INTERVAL '24 hours'
                    ) as uptime_24h
                FROM agent_cards a
                ORDER BY a.name
            """)
            
            return [dict(row) for row in rows]
    
    async def cleanup_old_health_history(self, days: int = 7) -> int:
        """Delete health history older than specified days"""
        async with self.connection() as conn:
            result = await conn.execute("""
                DELETE FROM health_check_history
                WHERE checked_at < NOW() - INTERVAL '%s days'
            """ % days)
            deleted = int(result.split()[-1]) if result else 0
            return deleted
    
    def _health_row_to_dict(self, row: Any) -> Dict[str, Any]:
        """Convert health check row to dictionary"""
        if not row:
            return None
        
        result = dict(row)
        
        # Convert UUID to string
        for field in ['id', 'agent_id']:
            if field in result and result[field]:
                result[field] = str(result[field])
        
        # Convert datetime
        if 'checked_at' in result and result['checked_at']:
            result['checked_at'] = result['checked_at'].isoformat()
        
        return result
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    def _row_to_dict(self, row: asyncpg.Record) -> Dict[str, Any]:
        """Convert asyncpg Record to dictionary with JSON parsing"""
        if not row:
            return None
        
        result = dict(row)
        
        # Convert UUID to string
        if 'id' in result and result['id']:
            result['id'] = str(result['id'])
        
        # Parse JSONB fields
        jsonb_fields = [
            'skills', 'capabilities', 'default_input_modes', 'default_output_modes',
            'provider', 'security_schemes', 'security', 'additional_interfaces', 'extensions'
        ]
        
        for field in jsonb_fields:
            if field in result and result[field]:
                if isinstance(result[field], str):
                    result[field] = json.loads(result[field])
        
        # Convert datetime to ISO format string
        datetime_fields = ['created_at', 'updated_at', 'last_seen', 'last_health_check']
        for field in datetime_fields:
            if field in result and result[field]:
                result[field] = result[field].isoformat()
        
        return result


# Global database instance
db = DatabaseManager()

