"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import ImageUploader from "@/components/ImageUploader";
import IngredientTags from "@/components/IngredientTags";
import Onboarding from "@/components/Onboarding";
import { useLocalStorage } from "@/lib/useLocalStorage";
import { UserProfile, LS_PROFILE } from "@/lib/types";

export default function Step1Page() {
  const router = useRouter();
  const [profile, setProfile, hydrated] = useLocalStorage<UserProfile | null>(LS_PROFILE, null);
  const [showOnboarding, setShowOnboarding] = useState(false);

  const [imageDataUrl, setImageDataUrl] = useState<string | null>(null);
  const [ingredients, setIngredients] = useState<{ text: string; auto: boolean }[]>([]);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeStep, setAnalyzeStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [analyzed, setAnalyzed] = useState(false);
  const analyzeTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // 첫 방문 시 온보딩 표시
  useEffect(() => {
    if (hydrated && !profile) setShowOnboarding(true);
  }, [hydrated, profile]);

  const handleImageSelect = useCallback((dataUrl: string) => {
    setImageDataUrl(dataUrl);
    setIngredients([]);
    setAnalyzed(false);
    setError(null);
  }, []);

  // 단계별 분석 메시지 순환
  const ANALYZE_STEPS = ["이미지 업로드 중...", "이미지 분석 중...", "재료를 인식하고 있어요..."];

  const handleAnalyze = async () => {
    if (!imageDataUrl) return;
    setAnalyzing(true);
    setAnalyzeStep(0);
    setError(null);

    // 1.2초마다 단계 메시지 순환
    analyzeTimerRef.current = setInterval(() => {
      setAnalyzeStep((prev) => (prev + 1) % ANALYZE_STEPS.length);
    }, 1200);

    try {
      const res = await fetch("/api/analyze-image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: imageDataUrl }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error ?? "알 수 없는 오류가 발생했습니다."); return; }
      setIngredients((data.ingredients as string[]).map((t) => ({ text: t, auto: true })));
      setAnalyzed(true);
      // [M-6] 썸네일 저장 — Base64 중간 절단 방지, QuotaExceededError 예외 처리
      try {
        sessionStorage.setItem("fridgeThumbnail", imageDataUrl);
      } catch {
        // 저장 공간 부족 시 썸네일 저장 skip (레시피 기능에는 영향 없음)
        sessionStorage.removeItem("fridgeThumbnail");
      }
    } catch {
      setError("네트워크 오류가 발생했습니다. 인터넷 연결을 확인해주세요.");
    } finally {
      setAnalyzing(false);
      if (analyzeTimerRef.current) {
        clearInterval(analyzeTimerRef.current);
        analyzeTimerRef.current = null;
      }
    }
  };

  const handleAddIngredient = (text: string) => {
    if (ingredients.find((i) => i.text === text)) return;
    setIngredients((prev) => [...prev, { text, auto: false }]);
  };
  const handleRemoveIngredient = (index: number) =>
    setIngredients((prev) => prev.filter((_, i) => i !== index));

  const handleGoToStep2 = () => {
    const list = ingredients.map((i) => i.text);
    sessionStorage.setItem("fridgeIngredients", JSON.stringify(list));
    // 프로필 식단 선호도 Step 2에 자동 반영
    if (profile?.dietPreferences?.length) {
      sessionStorage.setItem("fridgeProfileDiet", JSON.stringify(profile.dietPreferences));
    }
    // [M-8] 알레르기 정보를 sessionStorage를 통해 recipe 페이지에 전달
    if (profile?.allergies?.length) {
      sessionStorage.setItem("fridgeProfileAllergies", JSON.stringify(profile.allergies));
    } else {
      sessionStorage.removeItem("fridgeProfileAllergies");
    }
    router.push("/recipe");
  };

  const handleSaveProfile = (p: UserProfile) => {
    setProfile(p);
    setShowOnboarding(false);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50">
      {/* 온보딩 모달 */}
      {showOnboarding && (
        <Onboarding
          onSave={handleSaveProfile}
          onSkip={() => setShowOnboarding(false)}
        />
      )}

      <div className="max-w-xl mx-auto px-4 py-10">
        {/* 헤더 + 프로필 */}
        <div className="mb-8 text-center">
          <div className="flex items-center justify-end mb-2">
            {hydrated && profile ? (
              <button
                onClick={() => router.push("/profile")}
                className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700"
              >
                <span
                  style={{ backgroundColor: profile.avatarColor }}
                  className="w-7 h-7 rounded-full flex items-center justify-center text-base"
                >
                  {profile.avatar}
                </span>
                <span>{profile.nickname}</span>
              </button>
            ) : (
              <button
                onClick={() => setShowOnboarding(true)}
                className="text-xs text-blue-500 hover:underline"
              >
                프로필 설정
              </button>
            )}
            {hydrated && (
              <button
                onClick={() => router.push("/my-recipes")}
                className="ml-3 text-xs text-gray-400 hover:text-gray-600"
              >
                📚 레시피북
              </button>
            )}
          </div>

          <h1 className="text-3xl font-bold text-gray-800">🧊 냉장고 재료 인식</h1>
          <p className="mt-2 text-gray-500 text-sm">냉장고 사진을 업로드하면 AI가 재료를 자동으로 인식합니다</p>
          <div className="flex items-center justify-center gap-2 mt-5">
            <StepBadge num={1} label="재료 인식" active />
            <div className="w-8 h-px bg-gray-300" />
            <StepBadge num={2} label="레시피 생성" />
            <div className="w-8 h-px bg-gray-300" />
            <StepBadge num={3} label="저장" />
          </div>
        </div>

        <ImageUploader onImageSelect={handleImageSelect} imageDataUrl={imageDataUrl} />

        <button
          onClick={handleAnalyze}
          disabled={!imageDataUrl || analyzing}
          className="mt-4 w-full py-3 rounded-xl font-semibold text-white transition-all
            bg-blue-500 hover:bg-blue-600 active:scale-95
            disabled:bg-gray-300 disabled:cursor-not-allowed disabled:scale-100"
        >
          {analyzing ? (
            <span className="flex items-center justify-center gap-2">
              <Spinner />
              <span>{ANALYZE_STEPS[analyzeStep]}</span>
            </span>
          ) : "재료 인식하기"}
        </button>

        {error && (
          <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm flex items-start gap-2">
            <span className="shrink-0">⚠️</span>
            <div className="flex-1">
              <p>{error}</p>
              <button
                onClick={handleAnalyze}
                disabled={analyzing}
                className="mt-1 text-red-500 underline text-xs disabled:opacity-40 disabled:cursor-not-allowed"
              >
                다시 시도하기
              </button>
            </div>
          </div>
        )}

        {(analyzed || ingredients.length > 0) && (
          <div className="mt-6">
            <IngredientTags ingredients={ingredients} onAdd={handleAddIngredient} onRemove={handleRemoveIngredient} />
          </div>
        )}

        {ingredients.length > 0 && (
          <button
            onClick={handleGoToStep2}
            className="mt-6 w-full py-3 rounded-xl font-semibold text-white
              bg-emerald-500 hover:bg-emerald-600 active:scale-95 transition-all
              flex items-center justify-center gap-2"
          >
            레시피 추천받기 <span>→</span>
          </button>
        )}
      </div>
    </main>
  );
}

function StepBadge({ num, label, active }: { num: number; label: string; active?: boolean }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
        ${active ? "bg-blue-500 text-white" : "bg-gray-200 text-gray-400"}`}>{num}</div>
      <span className={`text-xs ${active ? "text-blue-600 font-semibold" : "text-gray-400"}`}>{label}</span>
    </div>
  );
}

function Spinner() {
  return (
    <svg aria-hidden="true" className="animate-spin h-4 w-4 text-white" viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  );
}
