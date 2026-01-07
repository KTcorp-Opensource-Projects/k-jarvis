# k-arc-utils Phase 5 (배포) 준비 완료

**작성일**: 2025-12-17  
**작성팀**: K-ARC Team  
**수신팀**: Orchestrator Team, Agent Team  
**상태**: ✅ GitHub Packages 배포 준비 완료

---

## 📦 패키지 정보 변경

### 배포 레지스트리 변경

| 항목 | 이전 | 변경 |
|------|------|------|
| **레지스트리** | npm (public) | **GitHub Packages** (private) |
| **패키지명** | `@k-arc/utils` | **`@ktspace/k-arc-utils`** |
| **버전** | 1.0.0-alpha.1 | **1.0.0** |
| **라이선스** | MIT | **UNLICENSED** (내부 전용) |

### 변경 이유

- 공개 npm 레지스트리 대신 **GitHub Enterprise 패키지 레지스트리** 사용
- 내부 전용 패키지로 **보안 및 접근 제어** 강화
- 사내 GitHub 조직(`@ktspace`)과 일관된 네이밍

---

## 🔧 설정 파일

### package.json 주요 설정

```json
{
  "name": "@ktspace/k-arc-utils",
  "version": "1.0.0",
  "license": "UNLICENSED",
  "private": false,
  "publishConfig": {
    "registry": "https://npm.pkg.github.com",
    "@ktspace:registry": "https://npm.pkg.github.com"
  },
  "repository": {
    "type": "git",
    "url": "https://github.ktspace.com/ktspace/k-arc-utils.git"
  }
}
```

### .npmrc 설정

```bash
@ktspace:registry=https://npm.pkg.github.com
```

---

## 📥 패키지 설치 방법 (사용자용)

### 1. GitHub 토큰 설정

프로젝트 루트에 `.npmrc` 파일 생성:

```bash
# .npmrc
@ktspace:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${GITHUB_TOKEN}
```

또는 로컬 `~/.npmrc`에 토큰 설정:

```bash
# ~/.npmrc
//npm.pkg.github.com/:_authToken=ghp_xxxxxxxxxxxx
```

### 2. 패키지 설치

```bash
npm install @ktspace/k-arc-utils
```

---

## 🚀 배포 방법

### GitHub Actions 자동 배포

`.github/workflows/publish.yml` 워크플로우가 설정되어 있습니다:

1. **Release 생성 시** 자동 배포
2. **수동 트리거** 가능 (workflow_dispatch)

```yaml
on:
  release:
    types: [published]
  workflow_dispatch:
```

### 수동 배포

```bash
cd packages/k-arc-utils

# 빌드
npm run build

# GitHub 토큰 설정 후 배포
npm publish
```

---

## 📋 사용 예시 업데이트

### 기존 (npm public)

```typescript
import { createUserContext } from '@k-arc/utils';
```

### 변경 후 (GitHub Packages)

```typescript
import { createUserContext } from '@ktspace/k-arc-utils';
```

---

## ✅ Phase 5 체크리스트

```markdown
### Phase 5: 배포
- [x] GitHub Packages 설정 완료
- [x] package.json 업데이트
- [x] .npmrc 설정
- [x] GitHub Actions 워크플로우 생성
- [x] README 업데이트
- [ ] GitHub Enterprise 레포지토리 생성 (요청 필요)
- [ ] 최초 배포 실행
- [ ] 다른 팀 설치 테스트
```

---

## 📋 다른 팀 요청 사항

### Orchestrator Team / Agent Team

`@ktspace/k-arc-utils` 또는 유사한 패키지를 사용하려면:

1. **GitHub 토큰 발급**
   - GitHub Enterprise에서 `read:packages` 권한이 있는 PAT 생성

2. **프로젝트 설정**
   - `.npmrc` 파일에 `@ktspace:registry` 설정 추가

3. **CI/CD 설정** (선택)
   - GitHub Actions에서 `GITHUB_TOKEN` 시크릿 사용

---

## 🗂️ 파일 구조

```
packages/k-arc-utils/
├── package.json            # GitHub Packages 설정 포함
├── .npmrc                  # 레지스트리 설정
├── .github/
│   └── workflows/
│       └── publish.yml     # 자동 배포 워크플로우
├── tsconfig.json
├── tsup.config.ts
├── README.md               # 설치 가이드 업데이트됨
└── src/                    # 소스 코드
```

---

## 📞 문의

- **GitHub Enterprise 레포지토리 생성** 관련 문의
- **토큰 발급** 관련 가이드 필요 시 연락

---

**K-ARC Team** 🌀

**k-arc-utils GitHub Packages 배포 준비 완료!** 🚀


