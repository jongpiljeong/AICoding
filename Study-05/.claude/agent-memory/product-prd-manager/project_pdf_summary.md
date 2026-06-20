---
name: PDF 문서 요약 웹 앱 프로젝트
description: 단일 HTML 파일로 구현하는 클라이언트 사이드 PDF 요약 앱의 핵심 결정 사항
type: project
---

PDF 문서 요약 웹 앱 (`index_pdf.html`) PRD 작성 완료 (2026-04-12).

**Why:** 서버 불필요, file:// 프로토콜에서 직접 실행, OpenRouter 무료 모델 활용, 비용 0원 운영이 핵심 제약.

**핵심 기술 결정:**
- PDF.js v3.11.174 (CDN: cdnjs) — v4는 file:// 환경에서 ES Module 문제
- OpenRouter 1순위 모델: `google/gemini-2.0-flash-exp:free`
- 텍스트 트리밍 기준: 12,000자 (약 3,000~4,000 토큰, 한국어 기준)
- API Key: sessionStorage 임시 저장 (하드코딩 절대 금지)
- localStorage 히스토리: 최근 5개, 저장 실패 시 오래된 항목 자동 삭제

**주요 에러 케이스:** ERR-001~010 (비PDF, 20MB초과, 스캔PDF, CDN실패, 인증오류, Rate Limit, 5xx, 네트워크, 스토리지, 추출오류)

**Open Question:** file:// Origin에서 OpenRouter CORS 허용 여부 사전 테스트 필수.

**How to apply:** 동일 프로젝트 내 추가 기능 PRD 또는 구현 가이드 작성 시 위 결정 사항을 기준으로 삼는다.
