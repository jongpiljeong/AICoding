---
name: AI 공감 다이어리 프로젝트 개요
description: 단일 index.html 파일로 동작하는 브라우저 전용 AI 감정 다이어리 앱 구조와 기술 결정 사항
type: project
---

단일 `index.html` 파일 안에 모든 로직(UI + API 호출 + 스토리지)이 포함된 서버리스 브라우저 앱.

**Why:** 별도 서버 없이 개인 로컬 환경에서만 실행하는 용도이므로 번들러/서버 없이 순수 HTML+JS로 구성.

**How to apply:** 새 기능 요청 시 단일 파일 구조를 유지하고 npm/번들러 도입은 사용자가 명시적으로 요청할 때만 권장.

## 핵심 기술 결정
- **API**: OpenRouter (`https://openrouter.ai/api/v1`), 모델 `deepseek/deepseek-chat-v3-0324:free`
- **API 키 위치**: `index.html` 상단 JS 상수 (`API_KEY`) — 개인 로컬 전용이므로 허용, 절대 git 커밋 금지
- **스토리지**: `localStorage` (키: `ai_diary_entries`), 30일 TTL 자동 정리
- **언어**: 응답은 한국어 강제, 시스템 프롬프트로 JSON 형식 고정

## 응답 스키마
```json
{ "emotion": "", "emotionEmoji": "", "empathyMessage": "", "encouragement": "" }
```

## 주요 함수
- `analyzeEmotion(diaryText)` — fetch + async/await, 에러 3계층 처리(네트워크/HTTP/JSON)
- `saveDiaryEntry(text, analysis)` — 저장 전 clearOldEntries() 자동 호출
- `loadDiaryEntries()` — 손상 데이터 방어 처리 포함
- `clearOldEntries()` — 30일 초과 항목 필터링
