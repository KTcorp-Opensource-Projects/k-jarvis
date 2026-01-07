# Contributing to K-Jarvis

K-Jarvis에 기여해 주셔서 감사합니다! 🎉

이 문서는 K-Jarvis 프로젝트에 기여하는 방법을 안내합니다.

---

## 📋 목차

- [행동 강령](#행동-강령)
- [시작하기](#시작하기)
- [기여 방법](#기여-방법)
- [개발 환경 설정](#개발-환경-설정)
- [코드 스타일](#코드-스타일)
- [Pull Request 프로세스](#pull-request-프로세스)
- [커뮤니티](#커뮤니티)

---

## 📜 행동 강령

이 프로젝트의 모든 참여자는 [Code of Conduct](CODE_OF_CONDUCT.md)를 준수해야 합니다.

**핵심 원칙:**
- 🤝 서로를 존중하고 배려합니다
- 🌍 다양성을 환영합니다
- 💬 건설적인 피드백을 제공합니다
- 🚫 차별과 괴롭힘을 금지합니다

---

## 🚀 시작하기

### 1. 저장소 Fork

GitHub에서 K-Jarvis 저장소를 Fork합니다.

### 2. 로컬에 Clone

```bash
git clone https://github.com/YOUR_USERNAME/k-jarvis.git
cd k-jarvis
```

### 3. Upstream 설정

```bash
git remote add upstream https://github.com/kt-jarvis/k-jarvis.git
```

### 4. 최신 코드 동기화

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

---

## 🎯 기여 방법

### 버그 리포트 🐛

버그를 발견하셨나요? [Issue](https://github.com/kt-jarvis/k-jarvis/issues/new?template=bug_report.md)를 생성해 주세요.

**좋은 버그 리포트:**
- 명확한 제목
- 재현 방법 (단계별로)
- 예상 동작 vs 실제 동작
- 환경 정보 (OS, Python 버전, 등)
- 스크린샷이나 로그 (가능하면)

### 기능 제안 💡

새로운 기능을 제안하고 싶으신가요?

1. 먼저 [Discussions](https://github.com/kt-jarvis/k-jarvis/discussions)에서 아이디어를 논의해 주세요
2. 논의 후 [Feature Request Issue](https://github.com/kt-jarvis/k-jarvis/issues/new?template=feature_request.md)를 생성해 주세요

### 문서 개선 📚

문서 개선도 소중한 기여입니다!

- 오타 수정
- 불명확한 설명 개선
- 예제 추가
- 번역

### 코드 기여 💻

1. 작업할 Issue를 선택하거나 새로 생성합니다
2. 브랜치를 생성합니다
3. 코드를 작성합니다
4. 테스트를 작성합니다
5. Pull Request를 생성합니다

---

## 🛠️ 개발 환경 설정

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+ (또는 Docker)

### Backend 설정

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발 의존성

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 필요한 값 설정

# DB 실행 (Docker)
docker-compose up -d postgres redis

# 테스트 실행
pytest tests/ -v

# 서버 실행
python run_orchestrator.py
```

### Frontend 설정

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env

# 개발 서버 실행
npm start

# 테스트 실행
npm test

# 빌드
npm run build
```

### Docker 전체 환경

```bash
# 전체 스택 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 종료
docker-compose down
```

---

## 📝 코드 스타일

### Python

**도구:**
- `black` - 코드 포매터
- `isort` - import 정렬
- `flake8` - 린터
- `mypy` - 타입 체킹

```bash
# 포맷팅 실행
black app/
isort app/

# 린팅 확인
flake8 app/
mypy app/
```

**규칙:**
- 들여쓰기: 4 spaces
- 줄 길이: 88자 (black 기본값)
- Docstring: Google 스타일

```python
def example_function(param1: str, param2: int) -> dict:
    """
    함수에 대한 간단한 설명.

    Args:
        param1: 첫 번째 파라미터 설명
        param2: 두 번째 파라미터 설명

    Returns:
        반환값 설명

    Raises:
        ValueError: 에러 발생 조건
    """
    pass
```

### JavaScript/TypeScript

**도구:**
- `ESLint` - 린터
- `Prettier` - 포매터

```bash
# 포맷팅 실행
npm run format

# 린팅 확인
npm run lint
```

**규칙:**
- 들여쓰기: 2 spaces
- 세미콜론: 사용
- 따옴표: 작은따옴표

### Commit Messages

[Conventional Commits](https://www.conventionalcommits.org/) 규칙을 따릅니다.

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types:**
| Type | 설명 |
|------|------|
| `feat` | 새로운 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 변경 |
| `style` | 코드 포맷팅 (기능 변화 없음) |
| `refactor` | 리팩토링 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 설정 변경 |
| `perf` | 성능 개선 |

**예시:**
```
feat(router): add multi-LLM support

- Add Claude and Gemini client implementations
- Update LLMClientFactory with fallback logic
- Add configuration options in .env

Closes #123
```

---

## 🔄 Pull Request 프로세스

### 1. 브랜치 생성

```bash
git checkout -b feature/my-feature
# 또는
git checkout -b fix/bug-description
```

**브랜치 명명 규칙:**
- `feature/*` - 새 기능
- `fix/*` - 버그 수정
- `docs/*` - 문서
- `refactor/*` - 리팩토링

### 2. 작업 및 커밋

```bash
# 작업 수행
git add .
git commit -m "feat(router): add new routing logic"
```

### 3. 최신 코드와 동기화

```bash
git fetch upstream
git rebase upstream/main
```

### 4. Push

```bash
git push origin feature/my-feature
```

### 5. Pull Request 생성

GitHub에서 Pull Request를 생성합니다.

**PR 체크리스트:**
- [ ] 관련 Issue 번호 언급 (예: `Closes #123`)
- [ ] 테스트 통과
- [ ] 코드 스타일 준수
- [ ] 문서 업데이트 (필요 시)
- [ ] Breaking Change 여부 명시

### 6. 리뷰

- 최소 1명의 리뷰어 승인 필요
- CI/CD 테스트 통과 필요
- 피드백에 대응

### 7. 머지

리뷰 승인 후 메인테이너가 머지합니다.

---

## 🧪 테스트

### Backend 테스트

```bash
cd backend

# 전체 테스트
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=app --cov-report=html

# 특정 테스트만
pytest tests/test_router.py -v
```

### Frontend 테스트

```bash
cd frontend

# 전체 테스트
npm test

# 커버리지 포함
npm test -- --coverage

# Watch 모드
npm test -- --watch
```

---

## 📦 릴리즈 프로세스

릴리즈는 메인테이너가 진행합니다.

1. `develop` 브랜치에서 `release/vX.Y.Z` 브랜치 생성
2. 버전 업데이트 및 CHANGELOG 작성
3. QA 테스트
4. `main` 브랜치에 머지
5. 태그 생성
6. GitHub Release 및 Docker 이미지 배포

---

## 💬 커뮤니티

### 연락처

- **GitHub Issues**: 버그 리포트, 기능 요청
- **GitHub Discussions**: 질문, 아이디어 논의
- **Email**: opensource@kt.com

### 기여자 인정

모든 기여자는 README의 Contributors 섹션에 표시됩니다.

---

## 🙏 감사합니다!

K-Jarvis를 더 좋게 만들어 주셔서 감사합니다! 🎉

여러분의 기여가 AI 에이전트 생태계를 발전시킵니다.

