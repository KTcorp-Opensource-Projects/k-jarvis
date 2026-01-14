import json
from typing import List, Optional, Dict
from loguru import logger

from ..llm_client import get_llm_client, BaseLLMClient
from .enums import WorkflowStepStatus
from .schema import Workflow, WorkflowStep, SupervisorDecision

class SupervisorLLM:
    """
    Supervisor LLM that validates step results and decides next actions.
    
    This implements the LangGraph Supervisor pattern where a central LLM
    coordinates the workflow execution, validates results, and handles errors.
    """
    
    def __init__(self):
        self.llm_client: Optional[BaseLLMClient] = get_llm_client()
        self._available = self.llm_client is not None and self.llm_client.is_available()
        
        if self._available:
            logger.info("[SUPERVISOR] Supervisor LLM initialized")
        else:
            logger.warning("[WARN] Supervisor LLM not available (no LLM client)")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    async def validate_step_result(
        self,
        step: WorkflowStep,
        workflow: 'Workflow',
        available_agents: List[Dict]
    ) -> SupervisorDecision:
        """
        Validate the result of a completed step and decide next action.
        """
        if not self._available:
            # Default to continue if supervisor not available
            return SupervisorDecision(
                action="continue",
                reasoning="Supervisor LLM not available, auto-continuing",
                confidence=0.5
            )
        
        # Format agents for fallback options
        agent_names = [a.get('name', '') for a in available_agents]
        
        prompt = f"""당신은 멀티에이전트 워크플로우의 Supervisor입니다. 방금 완료된 스텝의 결과를 검증하고 다음 액션을 결정하세요.

## 워크플로우 정보
- 이름: {workflow.name}
- 설명: {workflow.description}
- 전체 스텝: {len(workflow.steps)}개
- 현재 스텝: {workflow.current_step_index + 1}번째

## 완료된 스텝
- 에이전트: {step.agent_name}
- 작업: {step.action}
- 상태: {step.status.value}
- 에러: {step.error or "없음"}

## 스텝 결과 (처음 1000자):
```
{step.output[:1000] if step.output else "(출력 없음)"}
```

## 사용 가능한 에이전트 (fallback 옵션):
{', '.join(agent_names)}

## 다음 스텝 정보:
{self._format_next_step(workflow)}

## 결정 기준 (중요: continue를 우선 선택하세요!):
1. **continue**: 스텝이 어느 정도 성공적으로 완료됨 -> 다음 스텝으로 진행 (권장)
2. **retry**: 명백한 네트워크/타임아웃 오류인 경우에만
3. **modify**: 완전히 잘못된 작업을 수행한 경우에만 (거의 사용하지 않음)
4. **fallback**: 에이전트가 완전히 실패하고 다른 에이전트가 더 적합한 경우에만
5. **skip**: 비필수 스텝이고 실패해도 워크플로우 진행 가능한 경우
6. **abort**: 복구 불가능한 치명적 오류만

**주의**: 결과가 비어있지 않고 관련 정보를 포함하면 "continue"를 선택하세요.
에이전트가 안내 메시지를 반환해도 작업을 수행한 것으로 간주하고 "continue"하세요.

## 응답 형식 (JSON):
{{
    "action": "continue|retry|modify|fallback|skip|abort",
    "reasoning": "결정 이유",
    "confidence": 0.0-1.0,
    "modified_task": "action이 modify인 경우 수정된 작업 지시",
    "fallback_agent": "action이 fallback인 경우 대체 에이전트 이름",
    "user_message": "사용자에게 전달할 메시지 (선택적)"
}}
"""
        
        try:
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            decision = SupervisorDecision(
                action=result.get("action", "continue"),
                reasoning=result.get("reasoning", "No reasoning provided"),
                confidence=result.get("confidence", 0.5),
                modified_task=result.get("modified_task"),
                fallback_agent_id=self._find_agent_id(result.get("fallback_agent"), available_agents),
                user_message=result.get("user_message")
            )
            
            logger.info(f"[SUPERVISOR] Supervisor decision: {decision.action} (confidence: {decision.confidence:.2f})")
            logger.debug(f"   Reasoning: {decision.reasoning}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Supervisor validation error: {e}")
            # Default to continue on error
            return SupervisorDecision(
                action="continue",
                reasoning=f"Supervisor error: {e}, defaulting to continue",
                confidence=0.3
            )
    
    async def decide_error_recovery(
        self,
        step: WorkflowStep,
        error: str,
        workflow: 'Workflow',
        available_agents: List[Dict]
    ) -> SupervisorDecision:
        """
        Decide how to recover from a step failure.
        """
        if not self._available:
            # Default recovery based on retry count
            if step.retry_count < 2:
                return SupervisorDecision(
                    action="retry",
                    reasoning="Supervisor unavailable, attempting retry",
                    confidence=0.4
                )
            elif not step.is_critical:
                return SupervisorDecision(
                    action="skip",
                    reasoning="Supervisor unavailable, skipping non-critical step",
                    confidence=0.4
                )
            else:
                return SupervisorDecision(
                    action="abort",
                    reasoning="Supervisor unavailable, aborting after max retries",
                    confidence=0.4
                )
        
        # Format available agents
        agents_info = "\\n".join([
            f"- {a.get('name')}: {a.get('description', '')[:100]}"
            for a in available_agents
        ])
        
        prompt = f"""당신은 멀티에이전트 워크플로우의 Supervisor입니다. 스텝 실행 중 오류가 발생했습니다. 복구 전략을 결정하세요.

## 실패한 스텝
- 에이전트: {step.agent_name}
- 작업: {step.action}
- 재시도 횟수: {step.retry_count}
- 필수 스텝 여부: {'예' if step.is_critical else '아니오'}

## 오류 내용:
```
{error}
```

## 사용 가능한 대체 에이전트:
{agents_info}

## 복구 전략 옵션:
1. **retry**: 일시적 오류로 보임, 재시도 (최대 3회)
2. **modify**: 작업 지시를 수정하여 재시도 (예: 파라미터 변경)
3. **fallback**: 다른 에이전트로 대체 시도
4. **skip**: 비필수 스텝이므로 건너뛰기
5. **abort**: 복구 불가, 워크플로우 중단

## 응답 형식 (JSON):
{{
    "action": "retry|modify|fallback|skip|abort",
    "reasoning": "결정 이유",
    "confidence": 0.0-1.0,
    "modified_task": "action이 modify인 경우 수정된 작업",
    "fallback_agent": "action이 fallback인 경우 대체 에이전트",
    "user_message": "사용자에게 전달할 복구 상태 메시지"
}}
"""
        
        try:
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            decision = SupervisorDecision(
                action=result.get("action", "abort"),
                reasoning=result.get("reasoning", "Error recovery decision"),
                confidence=result.get("confidence", 0.5),
                modified_task=result.get("modified_task"),
                fallback_agent_id=self._find_agent_id(result.get("fallback_agent"), available_agents),
                user_message=result.get("user_message")
            )
            
            logger.info(f"[RECOVERY] Supervisor recovery decision: {decision.action}")
            logger.debug(f"   Reasoning: {decision.reasoning}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Supervisor recovery error: {e}")
            return SupervisorDecision(
                action="abort",
                reasoning=f"Supervisor error during recovery: {e}",
                confidence=0.2
            )
    
    def _format_next_step(self, workflow: 'Workflow') -> str:
        """Format information about the next step"""
        next_idx = workflow.current_step_index + 1
        if next_idx < len(workflow.steps):
            next_step = workflow.steps[next_idx]
            return f"다음 스텝: {next_step.agent_name} - {next_step.action}"
        return "다음 스텝: 없음 (마지막 스텝)"
    
    def _find_agent_id(self, agent_name: Optional[str], agents: List[Dict]) -> Optional[str]:
        """Find agent ID by name"""
        if not agent_name:
            return None
        
        agent_name_lower = agent_name.lower()
        for agent in agents:
            if agent.get('name', '').lower() == agent_name_lower:
                return agent.get('id')
            # Partial match
            if agent_name_lower in agent.get('name', '').lower():
                return agent.get('id')
        
        return None

# Global supervisor instance
supervisor_llm = SupervisorLLM()
