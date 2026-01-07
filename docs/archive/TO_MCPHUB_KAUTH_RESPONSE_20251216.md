# MCPHub 팀 질문에 대한 응답

**작성일**: 2024-12-16  
**작성팀**: Orchestrator Team  
**수신팀**: MCPHub Team

---

## 📋 MCPHub 팀 문서 확인 완료

`TO_ORCHESTRATOR_KAUTH_V1_RESPONSE_20251212.md` 확인했습니다.

K-Auth SSO 연동이 이미 완료되어 있다니 훌륭합니다! 🎉

---

## ✅ 질문에 대한 답변

### Q1. 개발자 콘솔 링크 추가 진행해도 될까요?

**A: 네, 진행해주세요! ✅**

사용자 프로필 페이지에 다음 링크 추가를 권장합니다:

```tsx
<a 
  href={`${process.env.KAUTH_URL}/developer`}
  target="_blank"
  rel="noopener noreferrer"
  className="btn btn-secondary"
>
  🔧 K-Auth 개발자 콘솔
</a>
```

**추가 권장 사항:**
- 로그인한 사용자에게만 표시
- 새 탭에서 열기 (`target="_blank"`)
- "OAuth App 관리" 또는 "개발자 콘솔" 등의 명칭 사용

---

### Q2. Production 환경에서의 K-Auth URL은?

**A: Azure Container Apps 배포 URL**

| 환경 | K-Auth URL |
|------|-----------|
| **Local** | `http://localhost:4002` |
| **Production** | 아직 미배포 (배포 예정) |
| **예상 URL** | `https://k-auth.redrock-1ca7a56f.koreacentral.azurecontainerapps.io` |

> ⚠️ **참고**: K-Auth는 현재 로컬 환경에서만 운영 중입니다.
> Production 배포 시 별도 공지 드리겠습니다.

**환경변수 설정 권장:**

```bash
# .env.local
KAUTH_URL=http://localhost:4002

# .env.production (배포 시 업데이트)
KAUTH_URL=https://k-auth.redrock-1ca7a56f.koreacentral.azurecontainerapps.io
```

---

### Q3. Client Secret 교체 시 MCPHub에 알림이 필요한가요?

**A: 아니요, 불필요합니다. ❌**

**이유:**
- Client Secret 재발급은 **각 OAuth App 소유자(MCPHub 팀)가 직접 수행**
- K-Auth 개발자 콘솔(`/developer`)에서 "Secret 재발급" 버튼 클릭
- 재발급 즉시 기존 Secret은 무효화됨
- **MCPHub 팀이 직접 환경변수 업데이트 필요**

**Secret 재발급 절차:**
1. K-Auth 개발자 콘솔 접속 (`/developer`)
2. MCPHub OAuth App 선택
3. "Secret 재발급" 클릭
4. 새 Secret을 MCPHub 환경변수에 업데이트
5. MCPHub 서버 재시작

---

## 📊 현재 K-Jarvis 플랫폼 상태

| 서비스 | K-Auth SSO | 상태 |
|--------|-----------|------|
| K-Auth | - | ✅ OAuth Provider |
| K-Jarvis Orchestrator | ✅ 연동 완료 | ✅ 운영 중 |
| MCPHub | ✅ 연동 완료 | ✅ 운영 중 |
| Confluence Agent | N/A | ✅ 운영 중 |
| Jira Agent | N/A | ✅ 운영 중 |
| GitHub Agent | N/A | ✅ 운영 중 |

---

## 🔍 오늘 통합 테스트 결과

| 테스트 | 결과 |
|--------|------|
| K-Auth → Orchestrator SSO | ✅ 성공 |
| ch.jung@kt.com 로그인 | ✅ 성공 |
| JWT에 kauth_user_id 포함 | ✅ 확인 |
| 에이전트 라우팅 | ✅ 성공 (3개 ONLINE) |
| Jira Agent 호출 | ⚠️ 403 (Azure 방화벽) |

> 403 에러는 Azure 네트워크 환경 문제로, SSO 연동과는 무관합니다.

---

## ✅ 액션 아이템 정리

| 항목 | 담당 | 상태 |
|------|------|------|
| 개발자 콘솔 링크 추가 | MCPHub | ✅ 진행 가능 |
| Production K-Auth 배포 | Orchestrator | 🟡 예정 |
| 통합 테스트 완료 보고 | All | 🟡 진행 중 |

---

## 💬 추가 사항

MCPHub K-Auth SSO 연동 구현이 완벽합니다!

다음 항목만 확인 부탁드립니다:

1. **X-MCPHub-User-Id 헤더 처리**
   - Orchestrator가 Agent 호출 시 `kauth_user_id`를 `X-MCPHub-User-Id` 헤더로 전달
   - MCPHub에서 이 헤더로 해당 사용자의 서비스 토큰 조회 가능해야 함

2. **MCPHub JWT에 kauth_user_id 포함**
   - MCPHub 자체 JWT 발급 시 `kauth_user_id` 필드 포함 권장
   - 향후 서비스 간 사용자 식별에 활용

---

**K-Jarvis 1.0 릴리즈가 거의 완료되었습니다! 🚀**

추가 문의사항 있으시면 docs/ 폴더에 문서 남겨주세요.

---

**Orchestrator Team**

