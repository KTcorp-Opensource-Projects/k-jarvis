"""
Conversation Service - Database-backed conversation management
대화 기록을 PostgreSQL에 영구 저장하고 관리하는 서비스
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger
from sqlalchemy import text

from .database import get_db_session
from .models import Conversation, ChatMessage, MessageRole


class ConversationService:
    """
    Database-backed conversation service.
    대화와 메시지를 PostgreSQL에 저장/조회/삭제합니다.
    """
    
    async def create_conversation(
        self,
        user_id: str,
        title: str = "New Chat"
    ) -> Conversation:
        """Create a new conversation for a user."""
        async with get_db_session() as session:
            conversation_id = str(uuid.uuid4())
            
            await session.execute(
                text("""
                    INSERT INTO conversations (id, user_id, title)
                    VALUES (:id, :user_id, :title)
                """),
                {"id": conversation_id, "user_id": user_id, "title": title}
            )
            await session.commit()
            
            return Conversation(
                id=conversation_id,
                title=title,
                messages=[]
            )
    
    async def get_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Conversation]:
        """Get a conversation with all its messages."""
        async with get_db_session() as session:
            # Get conversation
            if user_id:
                result = await session.execute(
                    text("""
                        SELECT id, title, created_at, updated_at
                        FROM conversations
                        WHERE id = :id AND user_id = :user_id
                    """),
                    {"id": conversation_id, "user_id": user_id}
                )
            else:
                result = await session.execute(
                    text("""
                        SELECT id, title, created_at, updated_at
                        FROM conversations
                        WHERE id = :id
                    """),
                    {"id": conversation_id}
                )
            
            row = result.fetchone()
            if not row:
                return None
            
            # Get messages
            messages_result = await session.execute(
                text("""
                    SELECT id, role, content, agent_used, task_id, metadata, created_at
                    FROM messages
                    WHERE conversation_id = :conversation_id
                    ORDER BY created_at ASC
                """),
                {"conversation_id": conversation_id}
            )
            
            messages = []
            for msg_row in messages_result.fetchall():
                metadata = msg_row[5] or {}
                if msg_row[3]:  # agent_used
                    metadata["agent"] = msg_row[3]
                if msg_row[4]:  # task_id
                    metadata["task_id"] = msg_row[4]
                
                messages.append(ChatMessage(
                    id=str(msg_row[0]),
                    role=MessageRole(msg_row[1]),
                    content=msg_row[2],
                    metadata=metadata,
                    timestamp=msg_row[6]
                ))
            
            return Conversation(
                id=str(row[0]),
                title=row[1],
                messages=messages,
                created_at=row[2],
                updated_at=row[3]
            )
    
    async def list_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Conversation]:
        """List all conversations for a user."""
        async with get_db_session() as session:
            result = await session.execute(
                text("""
                    SELECT id, title, created_at, updated_at
                    FROM conversations
                    WHERE user_id = :user_id
                    ORDER BY updated_at DESC
                    LIMIT :limit
                """),
                {"user_id": user_id, "limit": limit}
            )
            
            conversations = []
            for row in result.fetchall():
                conversations.append(Conversation(
                    id=str(row[0]),
                    title=row[1],
                    messages=[],  # Don't load messages for list view
                    created_at=row[2],
                    updated_at=row[3]
                ))
            
            return conversations
    
    async def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        agent_used: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Add a message to a conversation."""
        import json as json_lib
        
        async with get_db_session() as session:
            message_id = str(uuid.uuid4())
            
            # Convert metadata to JSON string properly
            metadata_json = json_lib.dumps(metadata) if metadata else "{}"
            
            await session.execute(
                text("""
                    INSERT INTO messages (id, conversation_id, role, content, agent_used, task_id, metadata)
                    VALUES (:id, :conversation_id, :role, :content, :agent_used, :task_id, CAST(:metadata AS jsonb))
                """),
                {
                    "id": message_id,
                    "conversation_id": conversation_id,
                    "role": role.value,
                    "content": content,
                    "agent_used": agent_used,
                    "task_id": task_id,
                    "metadata": metadata_json
                }
            )
            
            # Update conversation's updated_at
            await session.execute(
                text("""
                    UPDATE conversations SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {"id": conversation_id}
            )
            
            await session.commit()
            
            msg_metadata = metadata or {}
            if agent_used:
                msg_metadata["agent"] = agent_used
            if task_id:
                msg_metadata["task_id"] = task_id
            
            return ChatMessage(
                id=message_id,
                role=role,
                content=content,
                metadata=msg_metadata
            )
    
    async def update_conversation_title(
        self,
        conversation_id: str,
        title: str
    ) -> bool:
        """Update conversation title."""
        async with get_db_session() as session:
            result = await session.execute(
                text("""
                    UPDATE conversations SET title = :title, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                """),
                {"id": conversation_id, "title": title}
            )
            await session.commit()
            return result.rowcount > 0
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Delete a conversation and all its messages."""
        async with get_db_session() as session:
            if user_id:
                result = await session.execute(
                    text("""
                        DELETE FROM conversations
                        WHERE id = :id AND user_id = :user_id
                    """),
                    {"id": conversation_id, "user_id": user_id}
                )
            else:
                result = await session.execute(
                    text("""
                        DELETE FROM conversations WHERE id = :id
                    """),
                    {"id": conversation_id}
                )
            
            await session.commit()
            return result.rowcount > 0
    
    async def get_or_create_conversation(
        self,
        conversation_id: Optional[str],
        user_id: str
    ) -> Conversation:
        """Get existing conversation or create new one."""
        if conversation_id:
            conversation = await self.get_conversation(conversation_id, user_id)
            if conversation:
                return conversation
        
        return await self.create_conversation(user_id)


# Global service instance
conversation_service = ConversationService()

