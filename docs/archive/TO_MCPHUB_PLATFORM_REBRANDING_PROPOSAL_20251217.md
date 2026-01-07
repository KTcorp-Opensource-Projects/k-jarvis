# 🎨 MCPHub 플랫폼 리브랜딩 제안

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team (K-Auth + K-Jarvis 담당)  
**수신팀**: MCPHub Team  
**유형**: 제안

---

## 📢 제안 배경

K-Jarvis 생태계의 **브랜드 일관성**을 위해 MCPHub 플랫폼의 리브랜딩을 제안드립니다.

### 현재 상황
| 플랫폼 | 이름 | 디자인 테마 |
|--------|------|------------|
| K-Auth | K-Auth | J.A.R.V.I.S 스타일 HUD |
| Orchestrator | **K-Jarvis** | Cyan/Teal 민트 색감, 미래지향적 |
| MCP 허브 | MCPHub | (현재 다른 디자인) |

### 제안 후
| 플랫폼 | 이름 | 디자인 테마 |
|--------|------|------------|
| K-Auth | K-Auth | J.A.R.V.I.S 스타일 HUD |
| Orchestrator | **K-Jarvis** | Cyan/Teal 민트 색감 |
| MCP 허브 | **K-ARC** | Arc Reactor 스타일 |

---

## 🏷️ 1. 이름 변경 제안

### MCPHub → K-ARC

| 항목 | 내용 |
|------|------|
| **새 이름** | **K-ARC** (KT Arc Reactor for Cloud) |
| **의미** | Iron Man의 Arc Reactor에서 영감 - 에너지 공급원처럼 모든 AI Agent에게 MCP 서버 연결을 제공 |
| **브랜드 일관성** | K-Auth, K-Jarvis, **K-ARC** - "K-" 접두사로 통일 |

### 네이밍 컨셉

```
K-ARC = KT + Arc Reactor

Arc Reactor가 Iron Man에게 에너지를 공급하듯,
K-ARC는 AI Agent들에게 MCP 서버 연결(에너지)을 공급한다.
```

---

## 🎨 2. 디자인 테마 제안

### 컨셉: "Dark Arc Reactor"

K-Jarvis의 민트/시안 색감과 **차별화**하면서도 **같은 세계관**을 유지

### 색상 팔레트 제안

```css
:root {
  /* 배경 - 더 어두운 톤 */
  --bg-primary: #0a0a0f;      /* 거의 검정에 가까운 다크 */
  --bg-secondary: #12121a;    /* 어두운 네이비 */
  --bg-tertiary: #1a1a2e;     /* 약간 밝은 다크 */
  
  /* Arc Reactor 블루 - K-Jarvis 민트와 차별화 */
  --arc-core: #4fc3f7;        /* 밝은 아크 블루 (코어) */
  --arc-glow: #29b6f6;        /* 아크 글로우 */
  --arc-ring: #0288d1;        /* 아크 링 */
  --arc-pulse: #81d4fa;       /* 펄스 애니메이션용 */
  
  /* 액센트 */
  --accent-primary: #4fc3f7;   /* 메인 액센트 (아크 블루) */
  --accent-secondary: #ff6f00; /* 경고/에너지 (오렌지) */
  --accent-success: #00e676;   /* 성공 */
  --accent-error: #ff5252;     /* 에러 */
  
  /* 텍스트 */
  --text-primary: #e0e0e0;
  --text-secondary: #9e9e9e;
  --text-accent: #4fc3f7;
  
  /* 보더/라인 */
  --border-primary: rgba(79, 195, 247, 0.3);
  --border-glow: rgba(79, 195, 247, 0.5);
}
```

### 비주얼 차이점

| 요소 | K-Jarvis | K-ARC (제안) |
|------|----------|-------------|
| **배경** | 다크 블루 (#0d1117) | **더 어두운 블랙** (#0a0a0f) |
| **메인 색상** | 민트/시안 (#00d4ff) | **아크 블루** (#4fc3f7) |
| **느낌** | 홀로그램 HUD | **Arc Reactor 글로우** |
| **애니메이션** | 스캔 라인, 깜빡임 | **펄스, 에너지 파동** |

### 로고 컨셉

```
      ╭─────────╮
     ╱    ◯    ╲      ← Arc Reactor 코어
    │  ╱─────╲  │     ← 에너지 링
    │ │ K-ARC │ │     
    │  ╲─────╱  │
     ╲    ◯    ╱
      ╰─────────╯
```

---

## 🖼️ 3. UI 컴포넌트 스타일 제안

### 카드 컴포넌트

```css
.arc-card {
  background: linear-gradient(
    135deg,
    rgba(79, 195, 247, 0.05) 0%,
    rgba(10, 10, 15, 0.9) 100%
  );
  border: 1px solid rgba(79, 195, 247, 0.2);
  border-radius: 8px;
  box-shadow: 
    0 0 20px rgba(79, 195, 247, 0.1),
    inset 0 0 20px rgba(79, 195, 247, 0.05);
}

.arc-card:hover {
  border-color: rgba(79, 195, 247, 0.5);
  box-shadow: 
    0 0 30px rgba(79, 195, 247, 0.2),
    inset 0 0 30px rgba(79, 195, 247, 0.1);
}
```

### 버튼 스타일

```css
.arc-button {
  background: linear-gradient(180deg, #4fc3f7 0%, #0288d1 100%);
  border: none;
  color: #0a0a0f;
  font-weight: bold;
  box-shadow: 0 0 15px rgba(79, 195, 247, 0.4);
  transition: all 0.3s ease;
}

.arc-button:hover {
  box-shadow: 
    0 0 25px rgba(79, 195, 247, 0.6),
    0 0 50px rgba(79, 195, 247, 0.3);
  transform: translateY(-2px);
}
```

### Arc Reactor 애니메이션 (로고/로딩)

```css
@keyframes arc-pulse {
  0%, 100% {
    box-shadow: 
      0 0 20px rgba(79, 195, 247, 0.4),
      0 0 40px rgba(79, 195, 247, 0.2);
  }
  50% {
    box-shadow: 
      0 0 30px rgba(79, 195, 247, 0.6),
      0 0 60px rgba(79, 195, 247, 0.3),
      0 0 80px rgba(79, 195, 247, 0.1);
  }
}

.arc-reactor-logo {
  animation: arc-pulse 2s ease-in-out infinite;
}
```

---

## 🔄 4. K-Jarvis vs K-ARC 비교

### 시각적 차이

```
K-Jarvis (Orchestrator)          K-ARC (MCP Hub)
┌─────────────────────┐          ┌─────────────────────┐
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │          │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
│  ░░ 민트/시안 ░░░  │          │  ░░ 아크 블루 ░░░  │
│  ░░░░░░░░░░░░░░░░  │          │  ░░░░░░░░░░░░░░░░  │
│  ▒▒ HUD 스타일 ▒▒  │          │  ▒▒ Reactor 글로우 ▒│
│  ░░░░░░░░░░░░░░░░  │          │  ░░░░░░░░░░░░░░░░  │
└─────────────────────┘          └─────────────────────┘
     다크 블루 배경                    더 어두운 블랙 배경
```

### 통일성 유지 요소

- 폰트: Orbitron (로고), IBM Plex Sans (본문)
- 레이아웃 구조: 유사한 그리드 시스템
- 인터랙션 패턴: 유사한 호버 효과
- 아이콘 스타일: 라인 아이콘 (Lucide/Heroicons)

---

## 📋 5. 적용 범위

| 항목 | 변경 내용 |
|------|----------|
| 플랫폼 이름 | MCPHub → **K-ARC** |
| 로고 | 새 Arc Reactor 스타일 로고 |
| 색상 팔레트 | 민트 제거, 아크 블루 적용 |
| 배경 | 더 어두운 톤으로 변경 |
| 애니메이션 | 펄스/글로우 효과 추가 |
| URL (선택) | mcphub → k-arc (도메인 변경 시) |

---

## 💬 의견 요청

이 제안에 대한 MCPHub 팀의 의견을 부탁드립니다:

1. **이름 변경** (MCPHub → K-ARC)에 동의하시나요?
2. **디자인 컨셉** (Arc Reactor 스타일)이 적절한가요?
3. **추가 아이디어**나 우려사항이 있으신가요?

---

## 📝 응답 문서

**파일명**: `TO_ORCHESTRATOR_REBRANDING_RESPONSE_20251217.md`

```markdown
# MCPHub 리브랜딩 제안 응답

**작성일**: 2024-12-17
**작성팀**: MCPHub Team

## 의견

### 1. 이름 변경 (MCPHub → K-ARC)
- [ ] 동의
- [ ] 수정 제안: _______________

### 2. 디자인 컨셉
- [ ] 동의
- [ ] 수정 제안: _______________

### 3. 추가 의견
- 

### 4. 적용 예상 일정
- 
```

---

**K-Jarvis 생태계의 브랜드 통일을 위해 적극적인 검토 부탁드립니다!** 🚀

**Orchestrator Team (K-Auth + K-Jarvis 담당)**

