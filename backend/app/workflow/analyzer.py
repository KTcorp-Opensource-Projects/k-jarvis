import json
from typing import List, Optional, Dict
from loguru import logger

from ..llm_client import get_llm_client, BaseLLMClient
from .schema import Workflow, WorkflowStep, RetryPolicy

class LLMWorkflowAnalyzer:
    """
    LLM-based workflow analyzer that dynamically determines
    if a request requires multiple agents and what the workflow should be.
    """
    
    def __init__(self):
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        self._use_llm = self.llm_client is not None and self.llm_client.is_available()
        
        if self._use_llm:
            logger.info("[LLM] LLM-based workflow analyzer initialized")
        else:
            logger.warning("[WARN] LLM not available, falling back to pattern-based analysis")
    
    def _format_agents_for_llm(self, agents: List[Dict]) -> str:
        """Format agent information for LLM prompt"""
        if not agents:
            return "사용 가능한 에이전트가 없습니다."
        
        lines = []
        for agent in agents:
            name = agent.get('name', 'Unknown')
            desc = agent.get('description', 'No description')
            agent_id = agent.get('id', '')
            
            skills = agent.get('skills', [])
            skill_names = [s.get('name', '') for s in skills if s.get('name')]
            skill_str = ', '.join(skill_names) if skill_names else 'None'
            
            lines.append(f"- **{name}** (ID: {agent_id})")
            lines.append(f"  설명: {desc}")
            lines.append(f"  스킬: {skill_str}")
            lines.append("")
        
        return "\\n".join(lines)
    
    async def analyze(
        self, 
        user_message: str, 
        available_agents: List[Dict],
        previous_response: Optional[str] = None
    ) -> Optional['Workflow']:
        """Analyze user message using LLM to detect multi-agent workflows."""
        if not self._use_llm:
            logger.debug("LLM not available, skipping LLM analysis")
            return None
        
        if not available_agents:
            logger.debug("No agents available, skipping workflow analysis")
            return None
        
        agents_info = self._format_agents_for_llm(available_agents)
        
        # Build context about previous response if available
        previous_context = ""
        if previous_response:
            truncated = previous_response[:1000] + "..." if len(previous_response) > 1000 else previous_response
            previous_context = f"""
이전 대화에서 Assistant의 마지막 응답:
```
{truncated}
```
사용자가 "이 결과를", "이거", "방금 결과" 등을 언급하면 위 내용을 참조하는 것입니다.
"""
        
        prompt = f"""당신은 멀티 에이전트 워크플로우 분석기입니다. 사용자 요청을 분석하여 여러 에이전트가 순차적으로 협력해야 하는지 판단하세요.

## 사용 가능한 에이전트:
{agents_info}

{previous_context}

## 사용자 요청:
"{user_message}"

## 분석 지침:
1. 요청이 단일 에이전트로 처리 가능하면 is_multi_step: false
2. 여러 에이전트가 순차적으로 협력해야 하면 is_multi_step: true
3. "이 결과를 저장해줘", "이걸 문서로 만들어줘" 등은 이전 응답을 사용한 체이닝입니다
4. "검색하고 정리해줘", "만들고 저장해줘" 등은 멀티스텝 워크플로우입니다

## 응답 형식 (JSON):
{{
    "is_multi_step": true/false,
    "steps": [
        {{
            "agent_name": "에이전트 이름 (정확히 매칭)",
            "agent_id": "에이전트 ID",
            "action": "수행할 작업 (간단히)",
            "task_description": "에이전트에게 전달할 상세 지시사항",
            "use_previous_output": true/false,
            "output_type": "text/json/yaml/document 등"
        }}
    ],
    "workflow_name": "워크플로우 이름 (예: search_and_save)",
    "workflow_description": "워크플로우 설명",
    "reasoning": "이 워크플로우를 선택한 이유"
}}

단일 에이전트로 충분한 경우:
{{
    "is_multi_step": false,
    "steps": [],
    "reasoning": "단일 에이전트로 처리 가능한 이유"
}}
"""
        
        try:
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            logger.debug(f"LLM workflow analysis result: {result}")
            
            if not result.get("is_multi_step", False):
                logger.info(f"[ANALYZE] Single-agent request detected: {result.get('reasoning', 'N/A')}")
                return None
            
            return self._build_workflow_from_llm(result, available_agents, previous_response)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM workflow analysis error: {e}")
            return None
    
    def _build_workflow_from_llm(
        self,
        llm_result: Dict,
        available_agents: List[Dict],
        previous_response: Optional[str]
    ) -> Optional[Workflow]:
        """Build a Workflow object from LLM analysis result"""
        
        steps_data = llm_result.get("steps", [])
        if not steps_data:
            return None
        
        agent_by_name = {a.get('name', '').lower(): a for a in available_agents}
        agent_by_id = {a.get('id', ''): a for a in available_agents}
        
        workflow_steps = []
        
        for i, step_data in enumerate(steps_data):
            agent_name = step_data.get("agent_name", "")
            agent_id = step_data.get("agent_id", "")
            
            agent = agent_by_id.get(agent_id) or agent_by_name.get(agent_name.lower())
            
            if not agent:
                for name_key, agent_obj in agent_by_name.items():
                    if agent_name.lower() in name_key or name_key in agent_name.lower():
                        agent = agent_obj
                        break
            
            if not agent:
                logger.warning(f"Agent not found: {agent_name} (ID: {agent_id})")
                continue
            
            task_desc = step_data.get("task_description", step_data.get("action", ""))
            use_previous = step_data.get("use_previous_output", False)
            
            if i == 0 and use_previous and previous_response:
                task_desc = f"""다음 내용을 처리해주세요:

```
{previous_response}
```

작업: {task_desc}"""
                use_previous = False
            
            step = WorkflowStep(
                agent_id=agent.get("id", ""),
                agent_name=agent.get("name", "Unknown Agent"),
                action=step_data.get("action", "process"),
                input_prompt=task_desc,
                task_description=task_desc,
                use_previous_output=use_previous if i > 0 else False,
                output_type=step_data.get("output_type", "text")
            )
            workflow_steps.append(step)
        
        if not workflow_steps:
            return None
        
        return Workflow(
            name=llm_result.get("workflow_name", "dynamic_workflow"),
            description=llm_result.get("workflow_description", "LLM generated workflow"),
            steps=workflow_steps,
            reasoning=llm_result.get("reasoning", ""),
            retry_policy=RetryPolicy()
        )


class PatternBasedWorkflowAnalyzer:
    """Legacy pattern-based workflow analyzer."""
    
    CHAIN_PATTERNS = [
        {
            "triggers": ["이 결과", "이걸", "이거", "위 내용", "방금 결과", "저장해줘", "문서로 만들어줘"],
            "target_keywords": ["confluence", "컨플루언스", "문서", "저장"],
            "chain_type": "save_previous_to_confluence"
        },
        {
            "triggers": ["이 결과", "이걸", "이거", "위 내용", "방금"],
            "target_keywords": ["요약", "정리", "분석"],
            "chain_type": "analyze_previous"
        }
    ]
    
    WORKFLOW_PATTERNS = [
        {
            "triggers": ["만들고", "생성하고", "작성하고"],
            "second_actions": ["저장", "문서로", "confluence", "컨플루언스"],
            "workflow_type": "create_and_save",
            "description": "콘텐츠 생성 후 문서 저장"
        },
        {
            "triggers": ["검색하고", "찾고", "조회하고"],
            "second_actions": ["정리", "요약", "문서로", "저장"],
            "workflow_type": "search_and_document",
            "description": "검색 후 결과 문서화"
        },
        {
            "triggers": ["분석하고", "확인하고"],
            "second_actions": ["보고서", "리포트", "문서"],
            "workflow_type": "analyze_and_report",
            "description": "분석 후 보고서 생성"
        }
    ]
    
    def analyze(
        self, 
        user_message: str, 
        available_agents: List[Dict],
        previous_response: Optional[str] = None
    ) -> Optional[Workflow]:
        message_lower = user_message.lower()
        
        for pattern in self.WORKFLOW_PATTERNS:
            has_trigger = any(t in message_lower for t in pattern["triggers"])
            has_second = any(s in message_lower for s in pattern["second_actions"])
            
            if has_trigger and has_second:
                logger.info(f"[PATTERN] Pattern detected: {pattern['workflow_type']}")
                return self._build_workflow(user_message, pattern, available_agents)
        
        if previous_response:
            for pattern in self.CHAIN_PATTERNS:
                has_trigger = any(t in message_lower for t in pattern["triggers"])
                has_target = any(t in message_lower for t in pattern["target_keywords"])
                
                if has_trigger and has_target:
                    logger.info(f"[PATTERN] Chain pattern detected: {pattern['chain_type']}")
                    return self._build_chain_workflow(
                        user_message, previous_response, pattern, available_agents
                    )
        
        return None
    
    def _find_agent_by_keywords(self, agents: List[Dict], keywords: List[str]) -> Optional[Dict]:
        for agent in agents:
            agent_text = f"{agent.get('name', '')} {agent.get('description', '')}".lower()
            skills = agent.get('skills', [])
            skill_text = " ".join([
                f"{s.get('name', '')} {s.get('description', '')} {' '.join(s.get('tags', []))}"
                for s in skills
            ]).lower()
            
            full_text = f"{agent_text} {skill_text}"
            
            if any(kw in full_text for kw in keywords):
                return agent
        return None
    
    def _build_chain_workflow(
        self,
        user_message: str,
        previous_response: str,
        pattern: Dict,
        available_agents: List[Dict]
    ) -> Optional[Workflow]:
        workflow = Workflow(
            name=pattern["chain_type"],
            description=f"이전 응답을 사용한 체이닝: {pattern['chain_type']}",
            reasoning="Pattern-based chain detection"
        )
        
        if pattern["chain_type"] == "save_previous_to_confluence":
            confluence_agent = self._find_agent_by_keywords(
                available_agents,
                ["confluence", "문서", "document", "wiki"]
            )
            
            if confluence_agent:
                workflow.steps = [
                    WorkflowStep(
                        agent_id=confluence_agent.get("id", ""),
                        agent_name=confluence_agent.get("name", "Confluence Agent"),
                        action="save_document",
                        input_prompt=f"""다음 내용을 Confluence 문서로 저장해주세요:

```
{previous_response}
```

문서 제목과 형식은 내용에 맞게 자동으로 결정해주세요.""",
                        task_description="이전 응답을 Confluence 문서로 저장",
                        use_previous_output=False
                    )
                ]
                return workflow
        
        return None
    
    def _build_workflow(
        self, 
        user_message: str, 
        pattern: Dict, 
        available_agents: List[Dict]
    ) -> Optional[Workflow]:
        workflow = Workflow(
            name=pattern["workflow_type"],
            description=pattern["description"],
            reasoning="Pattern-based workflow detection"
        )
        
        if pattern["workflow_type"] == "create_and_save":
            content_agent = self._find_agent_by_keywords(
                available_agents, 
                ["yaml", "kubernetes", "k8s", "config", "설정", "생성"]
            )
            
            confluence_agent = self._find_agent_by_keywords(
                available_agents,
                ["confluence", "문서", "document", "wiki"]
            )
            
            if confluence_agent:
                if content_agent:
                    workflow.steps = [
                        WorkflowStep(
                            agent_id=content_agent.get("id", ""),
                            agent_name=content_agent.get("name", "Content Agent"),
                            action="generate",
                            input_prompt=self._extract_first_task(user_message),
                            task_description="콘텐츠 생성",
                            output_type="yaml"
                        ),
                        WorkflowStep(
                            agent_id=confluence_agent.get("id", ""),
                            agent_name=confluence_agent.get("name", "Confluence Agent"),
                            action="save_document",
                            input_prompt="이전 결과를 Confluence 문서로 저장해주세요.",
                            task_description="생성된 콘텐츠를 Confluence에 저장",
                            use_previous_output=True
                        )
                    ]
                else:
                    workflow.steps = [
                        WorkflowStep(
                            agent_id=confluence_agent.get("id", ""),
                            agent_name=confluence_agent.get("name", "Confluence Agent"),
                            action="create_document",
                            input_prompt=user_message,
                            task_description="Confluence 문서 생성"
                        )
                    ]
                return workflow
        
        elif pattern["workflow_type"] == "analyze_and_report":
            jira_agent = self._find_agent_by_keywords(available_agents, ["jira", "이슈", "issue", "project", "프로젝트"])
            confluence_agent = self._find_agent_by_keywords(available_agents, ["confluence", "문서", "document", "wiki", "페이지"])
            
            if jira_agent and confluence_agent:
                jira_prompt = self._extract_analysis_task(user_message)
                confluence_task = self._extract_document_task(user_message)
                
                workflow.steps = [
                    WorkflowStep(
                        agent_id=jira_agent.get("id", ""),
                        agent_name=jira_agent.get("name", "Jira Agent"),
                        action="analyze",
                        input_prompt=jira_prompt,
                        task_description="Jira 이슈 현황 분석",
                        output_type="text"
                    ),
                    WorkflowStep(
                        agent_id=confluence_agent.get("id", ""),
                        agent_name=confluence_agent.get("name", "Confluence Agent"),
                        action="create_document",
                        input_prompt=confluence_task,
                        task_description="분석 결과를 Confluence 문서로 생성",
                        use_previous_output=True,
                        output_type="url"
                    )
                ]
                return workflow
            elif jira_agent:
                workflow.steps = [
                    WorkflowStep(
                        agent_id=jira_agent.get("id", ""),
                        agent_name=jira_agent.get("name", "Jira Agent"),
                        action="analyze",
                        input_prompt=user_message,
                        task_description="Jira 이슈 현황 분석"
                    )
                ]
                return workflow
        
        elif pattern["workflow_type"] == "search_and_document":
            jira_agent = self._find_agent_by_keywords(available_agents, ["jira", "이슈", "issue", "search", "검색"])
            confluence_agent = self._find_agent_by_keywords(available_agents, ["confluence", "문서", "document", "wiki"])
            
            if jira_agent and confluence_agent:
                search_prompt = self._extract_first_task(user_message)
                workflow.steps = [
                    WorkflowStep(
                        agent_id=jira_agent.get("id", ""),
                        agent_name=jira_agent.get("name", "Jira Agent"),
                        action="search",
                        input_prompt=search_prompt,
                        task_description="이슈 검색",
                        output_type="text"
                    ),
                    WorkflowStep(
                        agent_id=confluence_agent.get("id", ""),
                        agent_name=confluence_agent.get("name", "Confluence Agent"),
                        action="create_document",
                        input_prompt="검색 결과를 문서로 정리해주세요.",
                        task_description="검색 결과 문서화",
                        use_previous_output=True
                    )
                ]
                return workflow
        
        return None
    
    def _extract_analysis_task(self, message: str) -> str:
        connectors = ["그리고", "후에", "다음에", "그 결과", "바탕으로"]
        for conn in connectors:
            if conn in message:
                first_part = message.split(conn)[0]
                if not first_part.endswith("해줘") and not first_part.endswith("해주세요"):
                    first_part = first_part.rstrip("하고확인분석") + " 분석해줘. 통계, 담당자별 현황, 주의가 필요한 이슈를 포함해서 상세하게 분석해줘."
                return first_part
        
        if "분석" in message:
            return message.replace("문서 생성", "").replace("보고서 생성", "").replace("Confluence에", "").strip()
        return message
    
    def _extract_document_task(self, message: str) -> str:
        import re
        date_match = re.search(r'(\d+월\s*\d+일|\d+/\d+)', message)
        date_str = date_match.group(1) if date_match else "금일"
        project_match = re.search(r'([A-Z]+)\s*프로젝트', message)
        project_name = project_match.group(1) if project_match else ""
        
        if project_name:
            return f"'{date_str} {project_name} 프로젝트 주간 보고서' 제목의 Confluence 문서를 생성해줘. 분석적이고 체계적인 보고서로 만들어줘."
        else:
            return "이 분석 결과를 바탕으로 보고서 문서를 Confluence에 생성해줘. 체계적인 보고서로 만들어줘."
    
    def _extract_first_task(self, message: str) -> str:
        connectors = ["하고", "그리고", "후에", "다음에"]
        for conn in connectors:
            if conn in message:
                return message.split(conn)[0] + "해줘"
        return message


class HybridWorkflowAnalyzer:
    """Hybrid workflow analyzer: LLM first, pattern fallback."""
    
    def __init__(self):
        self.llm_analyzer = LLMWorkflowAnalyzer()
        self.pattern_analyzer = PatternBasedWorkflowAnalyzer()
        self._use_llm = self.llm_analyzer._use_llm
        
        if self._use_llm:
            logger.info("[HYBRID] Hybrid workflow analyzer: LLM primary, pattern fallback")
        else:
            logger.info("[PATTERN] Hybrid workflow analyzer: Pattern-based only (LLM unavailable)")
    
    async def analyze(
        self,
        user_message: str,
        available_agents: List[Dict],
        previous_response: Optional[str] = None
    ) -> Optional[Workflow]:
        # Try LLM analysis first
        if self._use_llm:
            try:
                workflow = await self.llm_analyzer.analyze(
                    user_message, 
                    available_agents, 
                    previous_response
                )
                if workflow:
                    workflow.metadata["analyzer"] = "llm"
                    return workflow
            except Exception as e:
                logger.warning(f"LLM analysis failed, falling back to pattern: {e}")
        
        # Fallback to pattern-based
        workflow = self.pattern_analyzer.analyze(
            user_message, 
            available_agents, 
            previous_response
        )
        if workflow:
            workflow.metadata["analyzer"] = "pattern"
        
        return workflow

# Global analyzer instance
workflow_analyzer = HybridWorkflowAnalyzer()

async def analyze_workflow(
    user_message: str,
    available_agents: List[Dict],
    previous_response: Optional[str] = None
) -> Optional[Workflow]:
    """Convenience function for async analysis"""
    return await workflow_analyzer.analyze(user_message, available_agents, previous_response)
