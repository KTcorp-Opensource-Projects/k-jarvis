import json
from typing import List, Optional, Dict
from loguru import logger
from ..llm_client import get_llm_client, BaseLLMClient
from .enums import HandoffReason
from .schema import HandoffRequest

class HandoffDetector:
    """
    Detects handoff requests in agent responses using LLM analysis.
    
    Agents can signal handoff requests by:
    1. Explicit JSON format: {"handoff": {"target": "Agent Name", "task": "..."}}
    2. Natural language: "This should be handled by [Agent Name]"
    3. Structured markers in response
    """
    
    # Keywords that may indicate handoff intent
    HANDOFF_KEYWORDS = [
        "should be handled by",
        "better suited for",
        "recommend using",
        "delegate to",
        "hand off to",
        "transfer to",
        "this requires",
        "need to use",
        "다른 에이전트",
        "에게 위임",
        "처리해야",
    ]
    
    def __init__(self):
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        self._use_llm = self.llm_client is not None and self.llm_client.is_available()
        
        if self._use_llm:
            logger.info("[HANDOFF] LLM-based handoff detector initialized")
        else:
            logger.info("[HANDOFF] Pattern-based handoff detector initialized (no LLM)")
    
    async def detect(
        self,
        agent_response: str,
        available_agents: List[Dict],
        current_agent_name: str
    ) -> Optional[HandoffRequest]:
        """
        Detect if an agent response contains a handoff request.
        """
        # First, try to detect explicit JSON handoff format
        explicit = self._detect_explicit_handoff(agent_response)
        if explicit:
            return explicit
        
        # Check for keyword patterns
        if not self._has_handoff_keywords(agent_response):
            return None
        
        # Use LLM for sophisticated detection
        if self._use_llm:
            return await self._llm_detect_handoff(
                agent_response,
                available_agents,
                current_agent_name
            )
        
        # Fallback to pattern detection
        return self._pattern_detect_handoff(
            agent_response,
            available_agents,
            current_agent_name
        )
    
    def _detect_explicit_handoff(self, response: str) -> Optional[HandoffRequest]:
        """Detect explicit JSON handoff format in response"""
        try:
            # Look for JSON block in response
            import re
            json_pattern = r'\{[^{}]*"handoff"[^{}]*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)
            
            for match in matches:
                try:
                    data = json.loads(match)
                    if "handoff" in data:
                        handoff = data["handoff"]
                        return HandoffRequest(
                            target_agent_name=handoff.get("target", ""),
                            task_description=handoff.get("task", handoff.get("description", "")),
                            reason=HandoffReason(handoff.get("reason", "specialized")),
                            reason_detail=handoff.get("reason_detail", ""),
                            context_data=handoff.get("context", {})
                        )
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            logger.debug(f"[HANDOFF] Explicit detection error: {e}")
        
        return None
    
    def _has_handoff_keywords(self, response: str) -> bool:
        """Check if response contains handoff-related keywords"""
        response_lower = response.lower()
        return any(kw in response_lower for kw in self.HANDOFF_KEYWORDS)
    
    async def _llm_detect_handoff(
        self,
        response: str,
        available_agents: List[Dict],
        current_agent: str
    ) -> Optional[HandoffRequest]:
        """Use LLM to detect handoff intent"""
        
        agents_info = "\\n".join([
            f"- {a.get('name')}: {a.get('description', '')[:100]}"
            for a in available_agents
            if a.get('name') != current_agent
        ])
        
        prompt = f'''Analyze if this agent response suggests handing off to another agent.

Current Agent: {current_agent}

Agent Response:
```
{response[:1500]}
```

Available Agents:
{agents_info}

If the response suggests another agent should handle something, respond with JSON:
{{
    "has_handoff": true,
    "target_agent": "Agent Name",
    "task": "What should be done",
    "reason": "out_of_scope|specialized|follow_up|dependency",
    "confidence": 0.0-1.0
}}

If no handoff is needed:
{{
    "has_handoff": false,
    "reason": "Why no handoff is needed"
}}
'''
        
        try:
            result = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(result)
            
            if data.get("has_handoff") and data.get("confidence", 0) > 0.6:
                logger.info(f"[HANDOFF] LLM detected handoff to {data.get('target_agent')}")
                return HandoffRequest(
                    target_agent_name=data.get("target_agent", ""),
                    task_description=data.get("task", ""),
                    reason=HandoffReason(data.get("reason", "specialized")),
                    reason_detail=f"Confidence: {data.get('confidence', 0):.0%}"
                )
            
            return None
            
        except Exception as e:
            logger.error(f"[HANDOFF] LLM detection error: {e}")
            return None
    
    def _pattern_detect_handoff(
        self,
        response: str,
        available_agents: List[Dict],
        current_agent: str
    ) -> Optional[HandoffRequest]:
        """Pattern-based handoff detection (fallback)"""
        
        response_lower = response.lower()
        
        for agent in available_agents:
            agent_name = agent.get('name', '')
            if agent_name == current_agent:
                continue
            
            # Check if agent name is mentioned with handoff keywords
            if agent_name.lower() in response_lower:
                for keyword in self.HANDOFF_KEYWORDS:
                    if keyword in response_lower:
                        logger.info(f"[HANDOFF] Pattern detected handoff to {agent_name}")
                        return HandoffRequest(
                            target_agent_name=agent_name,
                            task_description=f"Continue task based on: {response[:200]}",
                            reason=HandoffReason.SPECIALIZED,
                            reason_detail=f"Keyword match: {keyword}"
                        )
        
        return None

# Global handoff detector instance
handoff_detector = HandoffDetector()
