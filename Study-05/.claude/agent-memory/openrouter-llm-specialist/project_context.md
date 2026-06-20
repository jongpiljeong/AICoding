---
name: Study-05 프로젝트 컨텍스트
description: 프로젝트 파일 구조, 사용 모델, 환경 설정 요약
type: project
---

Study-05는 순수 클라이언트 사이드(file://) 단일 HTML 파일 AI 웹앱 프로젝트입니다.

**Why:** 서버 인프라 비용 0원, 설치 없이 HTML 파일만 열면 동작하는 경량 도구 목표.

**How to apply:** 서버사이드 로직, npm 패키지, 빌드 도구 없이 CDN과 fetch API만 사용.

## 주요 파일
- `index.html` — AI 공감 다이어리 (감정 분석)
- `index_pdf.html` — PDF 문서 요약기 (텍스트 추출 + AI 요약)
- `.env` — `OPENROUTER_API_KEY` 저장 (file:// 환경이라 JS 상수로 직접 사용)
- `prd_pdf_summary.md` — PDF 요약기 PRD

## API 설정
- Base URL: `https://openrouter.ai/api/v1`
- 모델 우선순위: `deepseek/deepseek-chat:free` → `google/gemini-2.0-flash-exp:free` → `qwen/qwen-2.5-72b-instruct:free`
- `max_tokens: 1000`, `temperature: 0.3` (요약 작업 기준)

## PDF 처리
- PDF.js CDN 3.11.174 사용 (workerSrc 별도 설정 필요)
- 텍스트 추출 후 최대 12,000자 잘라내기 (토큰 초과 방지)
- 스캔 이미지 PDF: 추출 텍스트 50자 미만이면 에러 처리
