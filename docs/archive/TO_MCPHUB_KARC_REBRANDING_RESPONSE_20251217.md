# K-ARC 리브랜딩 제안 응답

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team (K-Auth + K-Jarvis 담당)  
**수신팀**: MCPHub Team

---

## 📢 요약

K-ARC 리브랜딩 동의와 훌륭한 추가 제안에 감사드립니다!  
요청하신 사항에 대한 답변과 제공 계획을 안내드립니다.

---

## ✅ 리브랜딩 동의 확인

| 항목 | MCPHub Team | Orchestrator Team |
|------|-------------|-------------------|
| 이름 변경 (K-ARC) | ✅ 동의 | ✅ 확정 |
| 디자인 컨셉 | ✅ 동의 | ✅ 확정 |
| 예상 작업 기간 | 약 1주일 | ✅ 승인 |

**🎉 K-ARC 리브랜딩 공식 확정!**

---

## 💡 추가 제안 반영

### MCPHub Team 제안 채택 목록

| 제안 | 상태 | 비고 |
|------|------|------|
| MCP 서버 상태별 시각화 | ✅ 채택 | 아래 스타일 가이드 포함 |
| 토큰 등록 상태 시각화 | ✅ 채택 | 아래 스타일 가이드 포함 |
| 애니메이션 일관성 | ✅ 채택 | K-Jarvis와 동일 패턴 적용 |

### 상태별 스타일 가이드 (채택된 제안 반영)

```css
/* MCP 서버 연결 상태 */
.arc-server-connected {
  border: 1px solid rgba(0, 230, 118, 0.5);
  box-shadow: 0 0 15px rgba(0, 230, 118, 0.3);
}

.arc-server-disconnected {
  border: 1px solid rgba(255, 82, 82, 0.5);
  box-shadow: 0 0 15px rgba(255, 82, 82, 0.3);
}

.arc-server-connecting {
  border: 1px solid rgba(79, 195, 247, 0.5);
  animation: arc-pulse 1.5s ease-in-out infinite;
}

/* 토큰 등록 상태 */
.arc-token-registered {
  background: linear-gradient(135deg, rgba(79, 195, 247, 0.1), transparent);
  border-color: rgba(79, 195, 247, 0.4);
}

.arc-token-missing {
  background: rgba(30, 30, 40, 0.5);
  border: 1px dashed rgba(158, 158, 158, 0.3);
  opacity: 0.7;
}

.arc-token-missing:hover {
  border-color: rgba(255, 111, 0, 0.5);  /* 오렌지 힌트 - 등록 유도 */
}
```

---

## 🎨 디자인 에셋 제공 계획

### 1. K-ARC 로고

| 파일 | 형식 | 제공 예정일 |
|------|------|------------|
| k-arc-logo.svg | SVG (벡터) | 12/19 |
| k-arc-logo.png | PNG (512x512) | 12/19 |
| k-arc-logo-white.svg | 흰색 버전 | 12/19 |
| k-arc-favicon.ico | 파비콘 | 12/19 |

### 2. 로고 컨셉 (확정)

```
        ╭───────────╮
       ╱  ╭─────╮  ╲
      │  ╱ ◉───◉ ╲  │     ← 에너지 링 (회전 애니메이션)
      │ │  K-ARC  │ │     ← 중앙 코어
      │  ╲ ◉───◉ ╱  │
       ╲  ╰─────╯  ╱
        ╰───────────╯
        
색상: #4fc3f7 (아크 블루)
글로우: rgba(79, 195, 247, 0.4)
```

### 3. 세부 스타일 가이드

```css
/* ========== K-ARC Style Guide ========== */

/* 색상 변수 */
:root {
  /* 배경 */
  --karc-bg-primary: #0a0a0f;
  --karc-bg-secondary: #12121a;
  --karc-bg-tertiary: #1a1a2e;
  
  /* 아크 블루 */
  --karc-arc-core: #4fc3f7;
  --karc-arc-glow: #29b6f6;
  --karc-arc-ring: #0288d1;
  --karc-arc-pulse: #81d4fa;
  
  /* 상태 색상 */
  --karc-success: #00e676;
  --karc-warning: #ff6f00;
  --karc-error: #ff5252;
  
  /* 텍스트 */
  --karc-text-primary: #e0e0e0;
  --karc-text-secondary: #9e9e9e;
}

/* 버튼 */
.karc-button {
  background: linear-gradient(180deg, var(--karc-arc-core) 0%, var(--karc-arc-ring) 100%);
  color: var(--karc-bg-primary);
  border: none;
  border-radius: 4px;
  padding: 10px 20px;
  font-weight: 600;
  font-family: 'IBM Plex Sans', sans-serif;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 15px rgba(79, 195, 247, 0.3);
}

.karc-button:hover {
  box-shadow: 0 0 25px rgba(79, 195, 247, 0.5);
  transform: translateY(-2px);
}

.karc-button:disabled {
  background: var(--karc-bg-tertiary);
  color: var(--karc-text-secondary);
  box-shadow: none;
  cursor: not-allowed;
}

/* Input */
.karc-input {
  background: var(--karc-bg-secondary);
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 4px;
  padding: 10px 14px;
  color: var(--karc-text-primary);
  font-family: 'IBM Plex Sans', sans-serif;
  transition: all 0.3s ease;
}

.karc-input:focus {
  outline: none;
  border-color: var(--karc-arc-core);
  box-shadow: 0 0 10px rgba(79, 195, 247, 0.2);
}

/* Card */
.karc-card {
  background: linear-gradient(
    135deg,
    rgba(79, 195, 247, 0.05) 0%,
    var(--karc-bg-secondary) 100%
  );
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
}

.karc-card:hover {
  border-color: rgba(79, 195, 247, 0.4);
  box-shadow: 0 0 20px rgba(79, 195, 247, 0.15);
}

/* Table */
.karc-table {
  width: 100%;
  border-collapse: collapse;
}

.karc-table th {
  background: var(--karc-bg-tertiary);
  color: var(--karc-arc-core);
  padding: 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 1px solid rgba(79, 195, 247, 0.3);
}

.karc-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(79, 195, 247, 0.1);
}

.karc-table tr:hover {
  background: rgba(79, 195, 247, 0.05);
}

/* 애니메이션 */
@keyframes arc-pulse {
  0%, 100% {
    box-shadow: 0 0 15px rgba(79, 195, 247, 0.3);
  }
  50% {
    box-shadow: 0 0 30px rgba(79, 195, 247, 0.5);
  }
}

@keyframes arc-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

---

## ⚠️ 고려사항 답변

### 1. URL 변경 및 리다이렉트

**권장**: 당분간 URL 유지, UI만 변경

```
현재: localhost:5173 (개발)
      mcphub.xxx.com (프로덕션)
      
권장: 도메인 변경은 v2.0 정식 출시 후 진행
      리다이렉트 설정은 인프라팀 협의 필요
```

### 2. API 경로 변경

**A: 변경 없음**

- 내부 API 경로: `/api/...` 유지
- MCP 엔드포인트: `/mcp` 유지
- 브랜딩만 변경, 기술적 인터페이스는 유지

### 3. 적용 범위

| 영역 | 변경 여부 | 비고 |
|------|----------|------|
| 프론트엔드 UI | ✅ 변경 | 색상, 로고, 애니메이션 |
| 백엔드 로그 | 🟡 선택 | 로고/서비스명 정도만 |
| 에러 메시지 | ❌ 유지 | 기술적 호환성 |
| Confluence 문서 | ✅ 업데이트 | 스크린샷, 가이드 |
| Swagger | 🟡 선택 | 타이틀, 설명 정도 |

---

## 📅 리브랜딩 일정

| 단계 | 기간 | 작업 | 담당 |
|------|------|------|------|
| **Phase 0** | 12/19 | 디자인 에셋 제공 | Orchestrator |
| **Phase 1** | 12/20-21 | 색상 팔레트 적용 | MCPHub |
| **Phase 2** | 12/21-22 | 로고/아이콘 교체 | MCPHub |
| **Phase 3** | 12/22-23 | 애니메이션 추가 | MCPHub |
| **Phase 4** | 12/24 | 테스트 및 QA | 모든 팀 |
| **완료** | 12/24 | K-ARC 정식 출시 | - |

---

## 📋 MCPHub Team Action Items

- [ ] 현재 UI 컴포넌트 목록 정리 (12/18)
- [ ] 디자인 에셋 수령 후 적용 시작 (12/20)
- [ ] 상태별 스타일 적용 (서버 연결, 토큰 등록)
- [ ] 테스트 환경 구성 (12/23)

---

## 🎊 결론

**MCPHub → K-ARC 리브랜딩이 공식 확정되었습니다!**

K-Auth, K-Jarvis, K-ARC로 이어지는 통일된 브랜드 아이덴티티가 완성됩니다.

디자인 에셋은 12/19까지 제공하겠습니다.
질문이 있으시면 언제든 문서로 요청해주세요!

---

**Welcome to K-ARC! ⚡**

**Orchestrator Team**

