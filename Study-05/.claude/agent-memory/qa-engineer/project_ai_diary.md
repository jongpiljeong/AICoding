---
name: AI 공감 다이어리 프로젝트 아키텍처 및 주요 버그 이력
description: index.html 단일 파일 앱 구조, 핵심 버그 패턴, 보안 고려사항
type: project
---

단일 HTML 파일(index.html)로 구성된 브라우저 직접 실행(file://) AI 공감 일기 앱.
OpenRouter API(OpenAI 호환 엔드포인트)를 사용하며 localStorage로 히스토리 관리.

**Why:** 별도 빌드 시스템 없이 file:// 프로토콜로 직접 열리는 구조이므로 환경 변수 주입이 불가능. API 키는 소스 내 상수로만 관리 가능하며 커밋 금지가 핵심 보안 정책임.

**How to apply:** 코드 리뷰 시 API_KEY 상수가 실제 키 값으로 채워져 있으면 즉시 플레이스홀더로 교체하고 .gitignore 확인 권고.

## 발견된 주요 버그 패턴 (2026-04-12)

1. **CSS display:none + classList 애니메이션 트랩**: `.result-card`가 `display: none` 상태일 때 `classList.remove("visible")` → `void offsetHeight` → `classList.add("visible")` 패턴은 작동하지 않음. 반드시 `style.display = "block"` 설정 후 리플로우, 그 다음 클래스 추가 순서 필요. 숨길 때는 `style.display = ""`로 인라인 스타일 초기화 필수.

2. **escapeHtml null 안전성**: 원본 구현이 null/undefined 입력 시 TypeError. `if (str == null) return ""; String(str)...` 패턴으로 방어.

3. **히스토리 렌더링 부분적 XSS 보호**: `e.text`에만 escapeHtml 적용, `e.dateLabel`, `e.emotion`, `e.emotionEmoji`는 미적용 상태였음. 모든 사용자 유래 데이터 필드에 일괄 적용해야 함.

4. **clearOldEntries 중복 호출**: init()과 saveDiaryEntry() 양쪽에서 호출되어 페이지 로드 시 localStorage를 두 번 읽고 쓰는 낭비 발생. saveDiaryEntry() 내부 호출 제거.
