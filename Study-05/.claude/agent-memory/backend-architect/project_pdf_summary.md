---
name: PDF 문서 요약 앱 개요
description: index_pdf.html — PDF.js + OpenRouter API 기반 순수 클라이언트 사이드 PDF 요약 앱
type: project
---

단일 `index_pdf.html` 파일로 구성된 서버리스 PDF 요약 웹앱. `file://` 프로토콜에서 직접 실행 가능.

**Why:** 서버 인프라 비용 0원, 외부 서버로 파일 전송 없음, 설치 불필요한 경량 도구 요구사항.

**How to apply:** 새 기능 추가 시 단일 HTML 파일 구조와 순수 클라이언트 사이드 제약을 유지. 서버 컴포넌트 도입 금지.

## 핵심 기술 스택

- PDF 텍스트 추출: PDF.js v3.11.174 (CDN)
  - Worker: `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`
- AI 요약: OpenRouter API (OpenAI 호환), 모델 폴백 전략 (deepseek → gemini → qwen)
- 상태 저장: localStorage (히스토리 최대 10개, TTL 없음)
- API 키: 소스 내 하드코딩 (로컬 전용, 커밋 금지)

## 핵심 함수 설계

| 함수 | 반환 | 역할 |
|------|------|------|
| `validatePDFFile(file)` | `{valid, error}` | MIME/확장자 + 20MB 크기 검사 |
| `extractTextFromPDF(file, onProgress)` | `Promise<string>` | PDF.js로 페이지별 텍스트 추출, 페이지 구분자 삽입 |
| `truncateText(text, maxChars=12000)` | `{text, truncated, originalLength}` | 12,000자 초과 시 앞부분만 사용 |
| `summarizePDF(pdfText)` | `Promise<{oneline, points, keywords, conclusion}>` | OpenRouter API 호출, 모델 폴백 |

## 스캔 이미지 PDF 감지 로직

추출 텍스트에서 구분자·숫자·공백을 제거한 순수 텍스트가 50자 미만이면 에러 처리.
OCR 지원은 Phase 2 검토 사항.
