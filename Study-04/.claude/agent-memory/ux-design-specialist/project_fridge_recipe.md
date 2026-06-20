---
name: 냉장고를 부탁해 앱 UX 개선 이력
description: Next.js 14 냉장고 재료 인식 → AI 레시피 생성 앱의 구조, 컴포넌트 패턴, UX 개선 이력
type: project
---

## 앱 구조
- app/page.tsx — Step 1: 냉장고 이미지 업로드 → 재료 인식 (blue/cyan 테마)
- app/recipe/page.tsx — Step 2: 스트리밍 레시피 생성 (orange/amber 테마)
- app/profile/page.tsx — 사용자 프로필 편집
- app/my-recipes/page.tsx — 저장된 레시피 목록 (emerald/teal 테마)
- app/my-recipes/[id]/page.tsx — 레시피 상세 (별점, 메모, 즐겨찾기, 삭제)
- components/ImageUploader.tsx, IngredientTags.tsx, RecipeCard.tsx, Onboarding.tsx, Toast.tsx

## 기술 스택
- Next.js 14 App Router, TypeScript, Tailwind CSS
- useLocalStorage 커스텀 훅 (lib/useLocalStorage.ts)
- sessionStorage로 페이지 간 데이터 전달 (재료, 썸네일, 프로필)
- OpenRouter API (스트리밍 레시피 생성)

## 적용된 UX 개선 (2026-04-13)
1. Toast.tsx: useRef로 onClose 고정 — 매 렌더마다 타이머 리셋되는 버그 수정
2. Onboarding.tsx: role="dialog", aria-modal="true", aria-labelledby, ESC 키 닫기, 아바타 버튼 aria-label/aria-pressed
3. app/page.tsx: 단계별 로딩 메시지 순환(이미지 업로드 중/분석 중/재료 인식 중), 다시시도 버튼 disabled={analyzing}, 스피너 aria-hidden
4. app/recipe/page.tsx: 스트리밍 취소 버튼 추가, 프로그레스 힌트 "(예상 30~60초)", 레시피 완료 후 "내 레시피북 보기" 링크, 스피너 aria-hidden
5. app/my-recipes/page.tsx: 레시피 0개 → 친근한 Empty State(냉장고 아이콘+CTA), 검색 결과 없음 → 별도 메시지+필터 초기화 버튼, 카드 버튼 aria-label
6. app/profile/page.tsx: 아바타 버튼 aria-label/aria-pressed
7. app/my-recipes/[id]/page.tsx: 뒤로가기 버튼 텍스트("← 내 레시피로") + aria-label, 즐겨찾기/삭제 버튼 aria-label, 별점 버튼 aria-label/aria-pressed
8. components/RecipeCard.tsx: 미보유 재료 주황+✗ 시각화(기존 파란 ~에서 변경), 범례 업데이트, 보유/미보유 sr-only 텍스트

## 컴포넌트 패턴
- Empty State: 큰 이모지 + 제목 + 설명 + CTA 버튼 구조
- 버튼 명명: 구체적 동사 ("냉장고 사진 찍으러 가기" vs "레시피 만들러 가기")
- 아바타/토글 버튼: aria-pressed 패턴 통일
- 스피너 SVG: aria-hidden="true" 필수

**Why:** 접근성 감사 및 사용자 경험 개선 요청으로 일괄 적용
**How to apply:** 추후 신규 컴포넌트 추가 시 위 패턴 동일 적용
