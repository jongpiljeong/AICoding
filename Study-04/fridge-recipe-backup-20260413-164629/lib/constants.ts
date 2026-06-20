// 앱 전체에서 공유하는 공통 상수

/** 식단 옵션 — Onboarding, recipe/page, profile/page 에서 공통 사용 */
export const DIET_OPTIONS = ["일반", "채식", "비건", "저칼로리", "글루텐 프리"] as const;
export type DietOption = (typeof DIET_OPTIONS)[number];
