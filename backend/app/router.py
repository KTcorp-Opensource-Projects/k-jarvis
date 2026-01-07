"""
Intelligent Agent Router
Uses LLM to analyze user intent and route to appropriate agents.
Supports both OpenAI and Azure OpenAI through abstraction layer.
"""
import json
from typing import Optional, List
from loguru import logger

from .config import get_settings
from .models import AgentInfo, Intent, RoutingDecision
from .registry import registry
from .llm_client import get_llm_client, BaseLLMClient


class IntentAnalyzer:
    """
    Analyzes user messages to understand intent and extract entities.
    Uses LLM for natural language understanding with keyword-based fallback.
    Supports OpenAI and Azure OpenAI via abstraction layer.
    """
    
    INTENT_PROMPT = """You are an intent classifier for an AI agent orchestration system.
Analyze the user's message and determine:
1. The primary intent category
2. Confidence level (0.0 to 1.0)
3. Relevant entities extracted from the message

Available intent categories:
- weather: Questions about weather, temperature, forecasts
- search: Web search, information lookup, research
- travel: Travel planning, bookings, destinations
- calendar: Scheduling, events, reminders
- calculator: Math calculations, unit conversions
- coding: Programming help, code generation, debugging
- general: General conversation, chitchat, unclear intent

Respond in JSON format:
{
    "category": "intent_category",
    "confidence": 0.95,
    "entities": {
        "location": "extracted location if any",
        "date": "extracted date if any",
        "query": "main query or topic"
    }
}

User message: {message}"""

    # Keyword-based intent detection (fallback when LLM unavailable)
    INTENT_KEYWORDS = {
        "weather": ["날씨", "기온", "온도", "비", "눈", "맑", "흐림", "weather", "temperature", "forecast", "rain", "sunny", "cloudy"],
        "search": ["검색", "찾아", "알려", "search", "find", "lookup", "what is", "who is"],
        "calculator": ["계산", "더하기", "빼기", "곱하기", "나누기", "+", "-", "*", "/", "%", "calculate", "math", "얼마"],
        "travel": ["여행", "비행", "호텔", "travel", "flight", "hotel", "booking"],
        "calendar": ["일정", "예약", "스케줄", "calendar", "schedule", "event", "meeting"],
        "coding": ["코드", "프로그램", "개발", "버그", "code", "program", "debug", "programming"],
    }

    def __init__(self):
        settings = get_settings()
        # Use the abstracted LLM client (supports OpenAI and Azure OpenAI)
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        self.use_llm = self.llm_client is not None and self.llm_client.is_available()
        
        if not self.use_llm:
            logger.warning("No LLM provider available - using keyword-based intent detection")
    
    def _keyword_analyze(self, message: str) -> Intent:
        """Keyword-based intent analysis (fallback)"""
        message_lower = message.lower()
        
        for category, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return Intent(
                        category=category,
                        confidence=0.8,
                        entities={"query": message}
                    )
        
        return Intent(category="general", confidence=0.5, entities={"query": message})
    
    async def analyze(self, message: str) -> Intent:
        """Analyze user message and return intent"""
        # Try keyword-based first for quick matching
        keyword_result = self._keyword_analyze(message)
        
        # If LLM not available or keyword match is strong, use keyword result
        if not self.use_llm:
            logger.info(f"Using keyword-based intent: {keyword_result.category}")
            return keyword_result
        
        try:
            # Use abstracted LLM client (supports OpenAI and Azure OpenAI)
            response = await self.llm_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an intent classification system. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": self.INTENT_PROMPT.format(message=message)
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            return Intent(
                category=result.get("category", "general"),
                confidence=result.get("confidence", 0.5),
                entities=result.get("entities", {})
            )
            
        except Exception as e:
            logger.error(f"LLM intent analysis failed: {e}")
            # Fallback to keyword-based
            return keyword_result


class AgentRouter:
    """
    Routes user requests to appropriate agents based on intent analysis.
    """
    
    ROUTING_PROMPT = """You are an agent routing system. Based on the user's intent and available agents, 
select the most appropriate agent to handle the request.

User message: {message}
Detected intent: {intent_category} (confidence: {confidence})
Extracted entities: {entities}

Available agents:
{agents_info}

Select the best agent and explain your reasoning.
If no suitable agent is found, respond with agent_id: null

Respond in JSON format:
{{
    "agent_id": "selected_agent_id or null",
    "agent_name": "agent name",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this agent was selected"
}}"""

    # Mapping of intent categories to agent skills/keywords
    INTENT_TO_SKILLS = {
        "weather": ["weather", "forecast", "temperature", "climate"],
        "search": ["search", "lookup", "find", "research", "web"],
        "travel": ["travel", "booking", "flight", "hotel", "destination"],
        "calendar": ["calendar", "schedule", "event", "reminder", "meeting"],
        "calculator": ["math", "calculate", "convert", "computation"],
        "coding": ["code", "programming", "debug", "development"],
    }

    def __init__(self):
        # Use the abstracted LLM client (supports OpenAI and Azure OpenAI)
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        self.use_llm = self.llm_client is not None and self.llm_client.is_available()
        self.intent_analyzer = IntentAnalyzer()
    
    async def route(self, message: str, enabled_agent_ids: Optional[List[str]] = None) -> Optional[RoutingDecision]:
        """
        Analyze message and route to the best agent.
        Returns None if no suitable agent is found.
        
        Args:
            message: User's message
            enabled_agent_ids: Optional list of agent IDs that user has enabled.
                              If provided, only these agents will be considered for routing.
        """
        # Get available agents
        all_agents = registry.list_agents()
        
        # Filter by enabled agents if provided
        if enabled_agent_ids is not None:
            agents = [a for a in all_agents if a.id in enabled_agent_ids]
            logger.info(f"Filtering to {len(agents)} enabled agents out of {len(all_agents)} total")
        else:
            agents = all_agents
        
        if not agents:
            logger.warning("No agents available for routing")
            return None
        
        # Analyze intent
        intent = await self.intent_analyzer.analyze(message)
        logger.info(f"Detected intent: {intent.category} (confidence: {intent.confidence})")
        
        # Try quick matching first (keyword-based)
        quick_match = self._quick_match(intent, agents, message)
        if quick_match:
            logger.info(f"Quick match found: {quick_match.agent_name}")
            return quick_match
        
        # Use LLM for more complex routing (if available)
        if self.use_llm:
            llm_result = await self._llm_route(message, intent, agents)
            if llm_result:
                return llm_result
        
        # Direct keyword matching on message as last resort
        direct_match = self._direct_keyword_match(message, agents)
        if direct_match:
            return direct_match
        
        return None
    
    def _quick_match(self, intent: Intent, agents: List[AgentInfo], message: str = "") -> Optional[RoutingDecision]:
        """
        Quick matching based on intent category and agent skills/description.
        """
        message_lower = message.lower()
        
        # ========================================
        # Priority 1: Explicit agent name in message
        # If user mentions a specific agent name, prioritize that agent
        # ========================================
        agent_keywords = {
            "jira": ["jira", "지라", "이슈", "티켓", "task"],
            "confluence": ["confluence", "컨플루언스", "문서", "페이지", "wiki"],
        }
        
        for agent_type, keywords_list in agent_keywords.items():
            if any(kw in message_lower for kw in keywords_list):
                for agent in agents:
                    if agent_type in agent.name.lower():
                        return RoutingDecision(
                            agent_id=agent.id,
                            agent_name=agent.name,
                            agent_url=agent.url,
                            confidence=0.95,
                            reasoning=f"Explicit agent reference: '{agent_type}' found in message"
                        )
        
        # ========================================
        # Priority 2: Intent-based matching
        # ========================================
        if intent.category == "general":
            # Still try to match based on message keywords
            return None
        
        keywords = self.INTENT_TO_SKILLS.get(intent.category, [])
        
        for agent in agents:
            # Check agent name and description
            agent_text = f"{agent.name} {agent.description}".lower()
            
            for keyword in keywords:
                if keyword in agent_text:
                    return RoutingDecision(
                        agent_id=agent.id,
                        agent_name=agent.name,
                        agent_url=agent.url,
                        confidence=intent.confidence * 0.9,
                        reasoning=f"Matched '{keyword}' in agent description for '{intent.category}' intent"
                    )
            
            # Check agent skills
            for skill in agent.skills:
                skill_text = f"{skill.name} {skill.description}".lower()
                skill_tags = " ".join(skill.tags).lower() if skill.tags else ""
                
                for keyword in keywords:
                    if keyword in skill_text or keyword in skill_tags:
                        return RoutingDecision(
                            agent_id=agent.id,
                            agent_name=agent.name,
                            agent_url=agent.url,
                            confidence=intent.confidence * 0.95,
                            reasoning=f"Matched skill '{skill.name}' for '{intent.category}' intent"
                        )
        
        return None
    
    def _direct_keyword_match(self, message: str, agents: List[AgentInfo]) -> Optional[RoutingDecision]:
        """
        Direct keyword matching from message to agent skills.
        Used as fallback when intent analysis doesn't find a match.
        """
        message_lower = message.lower()
        
        for agent in agents:
            # Check skill tags directly against message
            for skill in agent.skills:
                if skill.tags:
                    for tag in skill.tags:
                        if tag.lower() in message_lower:
                            return RoutingDecision(
                                agent_id=agent.id,
                                agent_name=agent.name,
                                agent_url=agent.url,
                                confidence=0.7,
                                reasoning=f"Direct keyword match: '{tag}' found in message"
                            )
                
                # Check skill examples
                if skill.examples:
                    for example in skill.examples:
                        # Check if message is similar to examples
                        example_words = set(example.lower().split())
                        message_words = set(message_lower.split())
                        common = example_words & message_words
                        if len(common) >= 2:
                            return RoutingDecision(
                                agent_id=agent.id,
                                agent_name=agent.name,
                                agent_url=agent.url,
                                confidence=0.65,
                                reasoning=f"Message similar to skill example: '{example}'"
                            )
        
        return None
    
    async def _llm_route(
        self,
        message: str,
        intent: Intent,
        agents: List[AgentInfo]
    ) -> Optional[RoutingDecision]:
        """
        Use LLM to select the best agent for complex routing decisions.
        Supports OpenAI and Azure OpenAI via abstraction layer.
        """
        # Format agents info
        agents_info = "\n".join([
            f"- ID: {a.id}\n  Name: {a.name}\n  Description: {a.description}\n  Skills: {[s.name for s in a.skills]}"
            for a in agents
        ])
        
        try:
            # Use abstracted LLM client (supports OpenAI and Azure OpenAI)
            response = await self.llm_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an intelligent agent routing system. Always respond with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": self.ROUTING_PROMPT.format(
                            message=message,
                            intent_category=intent.category,
                            confidence=intent.confidence,
                            entities=json.dumps(intent.entities),
                            agents_info=agents_info
                        )
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            if result.get("agent_id") is None:
                return None
            
            # Find the agent
            agent = registry.get_agent(result["agent_id"])
            if not agent:
                logger.warning(f"LLM selected unknown agent ID: {result['agent_id']}")
                return None
            
            return RoutingDecision(
                agent_id=agent.id,
                agent_name=agent.name,
                agent_url=agent.url,
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", "LLM routing decision")
            )
            
        except Exception as e:
            logger.error(f"LLM routing failed: {e}")
            return None


# Global router instance
router = AgentRouter()

