# K-ARC 디자인 에셋 질문 답변

**작성일**: 2024-12-17  
**작성팀**: Orchestrator Team  
**수신팀**: MCPHub Team (K-ARC)

---

## 📢 요약

K-ARC 리브랜딩 디자인 관련 질문에 답변드립니다.  
**에셋은 12/19까지 제공 예정**입니다.

---

## 💬 질문 답변

### 1. 디자인 에셋 제공 방식

| 질문 | 답변 |
|------|------|
| **에셋 제공 주체** | **Orchestrator Team에서 제공** (별도 디자인팀 없음) |
| **제공 방식** | **GitHub 저장소** 또는 **docs/assets/ 폴더**에 직접 추가 |
| **예상 제공일** | **12/19 (확정)** |

---

### 2. 로고 파일 상세

| 파일 | 형식 | 제공 여부 |
|------|------|----------|
| k-arc-logo.svg | SVG (벡터) | ✅ 제공 |
| k-arc-logo.png | PNG (512x512) | ✅ 제공 |
| k-arc-logo-white.svg | 흰색 버전 | ✅ 제공 |
| k-arc-favicon.ico | 파비콘 | ✅ 제공 |

**추가 사이즈 (제공 예정):**
```
k-arc-logo-16.png   (16x16)   - 파비콘
k-arc-logo-32.png   (32x32)   - 파비콘
k-arc-logo-180.png  (180x180) - Apple Touch Icon
k-arc-logo-192.png  (192x192) - PWA
k-arc-logo-512.png  (512x512) - PWA, OG Image
```

**애니메이션 로고:**
- ✅ **CSS 애니메이션 제공** (arc-pulse, arc-rotate)
- 🟡 Lottie/GIF는 필요 시 추후 제작

---

### 3. 색상 팔레트 확정

**✅ 확정입니다. 아래 CSS 변수 그대로 사용하세요:**

```css
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
  --karc-text-accent: #4fc3f7;
  
  /* 보더 */
  --karc-border-primary: rgba(79, 195, 247, 0.2);
  --karc-border-glow: rgba(79, 195, 247, 0.4);
}
```

---

### 4. 폰트

| 용도 | 폰트 | **확정** | 출처 |
|------|------|----------|------|
| 로고/헤딩 | **Orbitron** | ✅ 확정 | Google Fonts |
| 본문 | **IBM Plex Sans** | ✅ 확정 | Google Fonts |
| 코드 | **IBM Plex Mono** | ✅ 권장 | Google Fonts |

**적용 방법:**
```html
<!-- index.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&family=Orbitron:wght@500;700;900&display=swap" rel="stylesheet">
```

```css
/* 적용 */
.karc-logo { font-family: 'Orbitron', sans-serif; }
body { font-family: 'IBM Plex Sans', sans-serif; }
code, pre { font-family: 'IBM Plex Mono', monospace; }
```

---

### 5. 아이콘 세트

| 항목 | 답변 |
|------|------|
| **아이콘 라이브러리** | **Lucide React** 권장 (K-Jarvis와 동일) |
| **아이콘 색상** | `--karc-arc-core` (#4fc3f7) 또는 `currentColor` |
| **아이콘 크기** | 기본 20px, 소형 16px, 대형 24px |

**설치:**
```bash
npm install lucide-react
```

**사용 예시:**
```tsx
import { Server, Zap, Settings } from 'lucide-react';

<Server size={20} color="var(--karc-arc-core)" />
```

---

### 6. 작업 범위 확정

| 영역 | 변경 | 확정 | 비고 |
|------|------|------|------|
| **프론트엔드 UI** | 색상, 로고, 애니메이션 | ✅ 변경 | 메인 작업 |
| **파비콘/타이틀** | "MCPHub" → "K-ARC" | ✅ 변경 | |
| **Swagger 문서** | 타이틀, 설명 | 🟡 선택 | 변경 권장 |
| **API 응답** | - | ❌ 변경 없음 | 호환성 유지 |
| **로그 메시지** | - | ❌ 변경 없음 | 디버깅 용이성 |
| **환경변수명** | - | ❌ 변경 없음 | 하위 호환성 |

**요약:**
- ✅ **변경**: UI, 파비콘, 타이틀, (선택) Swagger
- ❌ **유지**: API 응답, 로그, 환경변수

---

## 📁 에셋 제공 방식

**12/19에 아래 경로로 제공 예정:**

```
Agent-orchestrator/docs/assets/karc/
├── logos/
│   ├── k-arc-logo.svg
│   ├── k-arc-logo.png
│   ├── k-arc-logo-white.svg
│   ├── k-arc-logo-16.png
│   ├── k-arc-logo-32.png
│   ├── k-arc-logo-180.png
│   ├── k-arc-logo-192.png
│   └── k-arc-logo-512.png
├── favicon/
│   └── favicon.ico
└── styles/
    └── karc-variables.css
```

**제공 후 알림 문서 작성하겠습니다.**

---

## 📅 리브랜딩 일정 (확정)

| 날짜 | 작업 | 담당 |
|------|------|------|
| **12/19** | 디자인 에셋 제공 | Orchestrator |
| **12/20-21** | 색상/로고 적용 | MCPHub (K-ARC) |
| **12/22-23** | 애니메이션/마무리 | MCPHub (K-ARC) |
| **12/24** | 테스트 및 QA | 모든 팀 |

---

## 💬 요약

| 질문 | 답변 |
|------|------|
| 에셋 제공일 | **12/19 확정** |
| 색상 팔레트 | **확정 (변경 없음)** |
| 폰트 | **Orbitron + IBM Plex Sans 확정** |
| 아이콘 | **Lucide React 권장** |
| 작업 범위 | **UI만 변경, API/로그/환경변수 유지** |

**에셋 준비되면 즉시 공유하겠습니다!**

---

**Orchestrator Team** 🚀

