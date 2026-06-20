---
name: summarizeText() 프롬프트 설계 패턴
description: PDF 요약 유형(full/bullets/oneline)별 시스템·사용자 프롬프트 설계 원칙
type: reference
---

## 핵심 원칙
- 시스템 프롬프트: 영어로 작성 → DeepSeek/Gemini/Qwen 모든 모델과 호환성 최대화
- 사용자 프롬프트: 한국어 요약 명시 + 출력 포맷 강제 (이중 제약)
- temperature: 0.3 — 요약은 창의성보다 일관성·정확성 우선

## full 타입 (전체 요약)
- 목표: 독자가 원본을 대신 읽은 효과
- 시스템: Markdown ## 제목 강제, 서론→본론→결론 구조 유지, 300-600자 목표
- 렌더링: ## 줄을 `<h3 class="summary-heading">`으로, 나머지를 `<p>`로 변환

## bullets 타입 (핵심 포인트)
- 목표: 10초 안에 핵심 파악 가능
- 시스템: EXACTLY 5-7개 강제, 각 bullet은 반드시 • (U+2022) 시작
- 렌더링: • 또는 - 로 시작하는 줄을 `<ul><li>` 변환, 후처리 파싱 단순화

## oneline 타입 (한 줄 요약)
- 목표: 슬라이드 자막/뉴스레터에 바로 사용 가능
- 시스템: EXACTLY 1문장, 50자 이내, 마침표로 끝 — 시스템+사용자 프롬프트 양쪽에 중복 명시
- 렌더링: `<p class="oneline-result">` 중앙 강조 표시

## HTTP 헤더 주의사항
- `HTTP-Referer`: ISO-8859-1 안전 문자만 (한글 금지 → `https://localhost` 사용)
- `X-Title`: ASCII only, 한글 절대 불가 (HTTP 헤더 규격) → `"PDF Summarizer"` 사용
