import uuid
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from ..llm_client import get_llm_client, BaseLLMClient
from .schema import Workflow

@dataclass
class MemoryEntry:
    """Single memory entry for long-term storage"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "conversation"  # conversation, workflow, artifact, fact
    content: str = ""
    summary: str = ""  # LLM-generated summary for quick retrieval
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None  # For vector search (optional)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    accessed_at: Optional[str] = None
    relevance_score: float = 0.0  # For search ranking
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content[:500],
            "summary": self.summary,
            "tags": self.tags,
            "created_at": self.created_at
        }

class MemoryStore:
    """
    Abstract memory store interface.
    Supports both in-memory and vector DB backends.
    """
    
    def __init__(self, max_entries: int = 1000):
        self.max_entries = max_entries
        self._entries: Dict[str, MemoryEntry] = {}
        self._index_by_type: Dict[str, List[str]] = {}
        self._index_by_tag: Dict[str, List[str]] = {}
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        
        logger.info(f"[MEMORY] Memory store initialized (max: {max_entries})")
    
    async def store(
        self,
        content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        generate_summary: bool = True
    ) -> MemoryEntry:
        """
        Store a new memory entry.
        """
        # Generate summary if LLM available
        summary = ""
        if generate_summary and self.llm_client and self.llm_client.is_available():
            summary = await self._generate_summary(content)
        
        entry = MemoryEntry(
            type=memory_type,
            content=content,
            summary=summary or content[:200],
            metadata=metadata or {},
            tags=tags or []
        )
        
        # Store entry
        self._entries[entry.id] = entry
        
        # Update indices
        if memory_type not in self._index_by_type:
            self._index_by_type[memory_type] = []
        self._index_by_type[memory_type].append(entry.id)
        
        for tag in (tags or []):
            if tag not in self._index_by_tag:
                self._index_by_tag[tag] = []
            self._index_by_tag[tag].append(entry.id)
        
        # Enforce max entries (LRU-style)
        if len(self._entries) > self.max_entries:
            await self._evict_oldest()
        
        logger.debug(f"[MEMORY] Stored entry {entry.id[:8]}... (type: {memory_type})")
        return entry
    
    async def retrieve(
        self,
        query: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """
        Retrieve relevant memories based on query.
        """
        candidates = []
        
        # Filter by type if specified
        if memory_type and memory_type in self._index_by_type:
            candidate_ids = self._index_by_type[memory_type]
        else:
            candidate_ids = list(self._entries.keys())
        
        # Filter by tags if specified
        if tags:
            tag_ids = set()
            for tag in tags:
                if tag in self._index_by_tag:
                    tag_ids.update(self._index_by_tag[tag])
            candidate_ids = [cid for cid in candidate_ids if cid in tag_ids]
        
        # Score candidates
        query_lower = query.lower()
        for cid in candidate_ids:
            entry = self._entries.get(cid)
            if not entry:
                continue
            
            # Simple relevance scoring
            score = 0.0
            content_lower = entry.content.lower()
            summary_lower = entry.summary.lower()
            
            # Exact match boost
            if query_lower in content_lower:
                score += 0.5
            if query_lower in summary_lower:
                score += 0.3
            
            # Word match
            query_words = query_lower.split()
            for word in query_words:
                if word in content_lower:
                    score += 0.1
                if word in summary_lower:
                    score += 0.05
            
            # Recency boost (newer = higher)
            try:
                created = datetime.fromisoformat(entry.created_at)
                age_hours = (datetime.now() - created).total_seconds() / 3600
                recency_score = max(0, 1 - (age_hours / 168))  # Decay over 1 week
                score += recency_score * 0.2
            except (ValueError, TypeError) as e:
                logger.debug(f"[MEMORY] Failed to parse created_at: {e}")
            
            entry.relevance_score = score
            if score > 0:
                candidates.append(entry)
        
        # Sort by relevance and return top results
        candidates.sort(key=lambda e: e.relevance_score, reverse=True)
        
        results = candidates[:limit]
        
        # Update access time
        for entry in results:
            entry.accessed_at = datetime.now().isoformat()
        
        logger.debug(f"[MEMORY] Retrieved {len(results)} entries for query: {query[:50]}")
        return results
    
    async def store_workflow_result(self, workflow: Workflow) -> MemoryEntry:
        """Store a completed workflow for future reference"""
        
        # Build content from workflow
        content_parts = [
            f"Workflow: {workflow.name}",
            f"Description: {workflow.description}",
            f"Status: {workflow.status.value}",
            f"Steps: {len(workflow.steps)}"
        ]
        
        for i, step in enumerate(workflow.steps):
            content_parts.append(f"  Step {i+1}: {step.agent_name} - {step.action}")
            if step.output:
                content_parts.append(f"    Output: {step.output[:200]}...")
        
        content = "\\n".join(content_parts)
        
        # Extract tags
        tags = ["workflow", workflow.name]
        for step in workflow.steps:
            tags.append(step.agent_name.lower().replace(" ", "_"))
        
        return await self.store(
            content=content,
            memory_type="workflow",
            metadata={
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "status": workflow.status.value,
                "steps_count": len(workflow.steps)
            },
            tags=list(set(tags))
        )
    
    async def get_relevant_context(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        limit: int = 3
    ) -> str:
        """
        Get relevant context from memory for a user message.
        Returns formatted context string for LLM consumption.
        """
        memories = await self.retrieve(
            query=user_message,
            limit=limit
        )
        
        if not memories:
            return ""
        
        context_parts = ["## Relevant Context from Memory:"]
        for i, mem in enumerate(memories):
            context_parts.append(f"\\n### Memory {i+1} ({mem.type}):")
            context_parts.append(mem.summary or mem.content[:300])
        
        return "\\n".join(context_parts)
    
    async def _generate_summary(self, content: str) -> str:
        """Generate a brief summary using LLM"""
        if not self.llm_client or not self.llm_client.is_available():
            return content[:200]
        
        try:
            result = await self.llm_client.chat_completion(
                messages=[{
                    "role": "user",
                    "content": f"Summarize in 1-2 sentences:\\n{content[:1000]}"
                }]
            )
            return result[:200]
        except Exception as e:
            logger.debug(f"[MEMORY] Summary generation failed: {e}")
            return content[:200]
    
    async def _evict_oldest(self):
        """Remove oldest entries when max is reached"""
        if len(self._entries) <= self.max_entries:
            return
        
        # Sort by created_at and remove oldest
        sorted_entries = sorted(
            self._entries.items(),
            key=lambda x: x[1].created_at
        )
        
        to_remove = len(self._entries) - self.max_entries
        for entry_id, _ in sorted_entries[:to_remove]:
            del self._entries[entry_id]
            # Clean up indices
            for type_list in self._index_by_type.values():
                if entry_id in type_list:
                    type_list.remove(entry_id)
            for tag_list in self._index_by_tag.values():
                if entry_id in tag_list:
                    tag_list.remove(entry_id)
        
        logger.debug(f"[MEMORY] Evicted {to_remove} old entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics"""
        return {
            "total_entries": len(self._entries),
            "max_entries": self.max_entries,
        }
memory_store = MemoryStore()
