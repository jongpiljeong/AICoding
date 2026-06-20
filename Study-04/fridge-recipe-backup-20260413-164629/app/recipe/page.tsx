"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import RecipeCard, { Recipe } from "@/components/RecipeCard";
import Toast from "@/components/Toast";
import { useLocalStorage } from "@/lib/useLocalStorage";
import { SavedRecipe, LS_RECIPES } from "@/lib/types";
// [m-6] 공통 상수에서 import
import { DIET_OPTIONS } from "@/lib/constants";

// ── 옵션 타입 ────────────────────────────────────────────────────────────────
interface Options {
  servings: number;
  maxTime: number | null;
  diet: string[];
  count: number;
}

const SERVINGS_OPTIONS = [
  { label: "1인", value: 1 },
  { label: "2인", value: 2 },
  { label: "4인+", value: 4 },
];
const TIME_OPTIONS = [
  { label: "15분", value: 15 },
  { label: "30분", value: 30 },
  { label: "1시간", value: 60 },
  { label: "무제한", value: null },
];
const COUNT_OPTIONS = [
  { label: "1개", value: 1 },
  { label: "3개", value: 3 },
  { label: "5개", value: 5 },
];

// ── JSON 파싱 헬퍼 ────────────────────────────────────────────────────────────
function parseRecipes(raw: string): Recipe[] | null {
  const match = raw.match(/\{[\s\S]*\}/);
  if (!match) return null;
  try {
    const parsed = JSON.parse(match[0]);
    const list: Recipe[] = (parsed.recipes ?? []).map((r: Omit<Recipe, "id">, i: number) => ({
      ...r,
      id: `recipe-${Date.now()}-${i}`,
    }));
    return list.length > 0 ? list : null;
  } catch {
    return null;
  }
}

// ── 메인 페이지 ──────────────────────────────────────────────────────────────
export default function RecipePage() {
  const router = useRouter();
  const [ingredients, setIngredients] = useState<string[]>([]);
  const [allergies, setAllergies] = useState<string[]>([]);
  const [options, setOptions] = useState<Options>({
    servings: 2,
    maxTime: 30,
    diet: ["일반"],
    count: 3,
  });

  const [status, setStatus] = useState<"idle" | "streaming" | "done" | "error">("idle");
  const [streamText, setStreamText] = useState("");
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set());
  const [errorMsg, setErrorMsg] = useState("");
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);
  const [savedRecipes, setSavedRecipes] = useLocalStorage<SavedRecipe[]>(LS_RECIPES, []);
  const abortRef = useRef<AbortController | null>(null);

  // [S-1] 스트리밍 throttle용 ref
  const accRef = useRef("");
  const lastFlushRef = useRef(0);

  // [M-1] 언마운트 시 진행 중인 fetch abort — 메모리 누수 방지
  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    // [M-2] sessionStorage 파싱 try/catch — 손상된 데이터로 인한 crash 방지
    const stored = sessionStorage.getItem("fridgeIngredients");
    if (stored) {
      try {
        setIngredients(JSON.parse(stored));
      } catch {
        sessionStorage.removeItem("fridgeIngredients");
      }
    }
    // 프로필 식단 자동 반영
    const profileDiet = sessionStorage.getItem("fridgeProfileDiet");
    if (profileDiet) {
      try {
        const diet = JSON.parse(profileDiet) as string[];
        if (diet.length) setOptions((p) => ({ ...p, diet }));
      } catch {
        sessionStorage.removeItem("fridgeProfileDiet");
      }
    }
    // [M-8] 알레르기 정보 sessionStorage에서 읽기
    const profileAllergies = sessionStorage.getItem("fridgeProfileAllergies");
    if (profileAllergies) {
      try {
        const parsed = JSON.parse(profileAllergies) as string[];
        if (Array.isArray(parsed)) setAllergies(parsed);
      } catch {
        sessionStorage.removeItem("fridgeProfileAllergies");
      }
    }
  }, []);

  // 식단 토글
  const toggleDiet = (d: string) =>
    setOptions((prev) => ({
      ...prev,
      diet: prev.diet.includes(d)
        ? prev.diet.filter((x) => x !== d)
        : [...prev.diet, d],
    }));

  // 레시피 생성
  const handleGenerate = async () => {
    if (ingredients.length === 0) return;
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setStatus("streaming");
    setStreamText("");
    setRecipes([]);
    setErrorMsg("");
    accRef.current = "";
    lastFlushRef.current = 0;

    try {
      const res = await fetch("/api/generate-recipe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // [M-8] 알레르기 정보를 options에 포함하여 API로 전달
        body: JSON.stringify({ ingredients, options: { ...options, allergies } }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "오류가 발생했습니다." }));
        throw new Error(err.error);
      }

      // [M-7] res.body null 체크
      if (!res.body) throw new Error("응답 스트림을 받을 수 없습니다.");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      // [S-1] useRef로 accumulated 관리, 100ms throttle로 리렌더링 최소화
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        accRef.current += chunk;
        const now = Date.now();
        if (now - lastFlushRef.current > 100) {
          setStreamText(accRef.current);
          lastFlushRef.current = now;
        }
      }
      // 루프 종료 후 최종 flush
      setStreamText(accRef.current);

      // 스트림 완료 후 JSON 파싱
      const parsed = parseRecipes(accRef.current);
      if (parsed) {
        setRecipes(parsed);
        setStatus("done");
        // sessionStorage에 보관
        sessionStorage.setItem("fridgeRecipes", JSON.stringify(parsed));
      } else {
        throw new Error("레시피 형식을 파싱할 수 없습니다. 다시 시도해주세요.");
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.name === "AbortError") return;
      setErrorMsg(e instanceof Error ? e.message : "알 수 없는 오류");
      setStatus("error");
    }
  };

  // 저장하기 (localStorage)
  const handleSave = (recipe: Recipe) => {
    const isDup = savedRecipes.find((r) => r.title === recipe.title);
    if (isDup) {
      if (!confirm(`"${recipe.title}"은(는) 이미 저장되어 있습니다. 덮어쓸까요?`)) return;
    }

    const thumbnail = sessionStorage.getItem("fridgeThumbnail") ?? null;
    const sourceIngredients = ingredients;

    const saved: SavedRecipe = {
      ...recipe,
      thumbnail,
      savedAt: new Date().toISOString(),
      rating: null,
      memo: "",
      isFavorite: false,
      sourceIngredients,
    };

    if (isDup) {
      setSavedRecipes((prev) => prev.map((r) => (r.title === recipe.title ? saved : r)));
    } else {
      if (savedRecipes.length >= 100) {
        setToast({ message: "레시피 저장 한도(100개)에 도달했습니다.", type: "error" });
        return;
      }
      setSavedRecipes((prev) => [saved, ...prev]);
    }

    setSavedIds((prev) => new Set(Array.from(prev).concat(recipe.id)));
    setToast({ message: `"${recipe.title}" 저장 완료!`, type: "success" });
  };

  const isGenerating = status === "streaming";

  return (
    <main className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50">
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
      <div className="max-w-xl mx-auto px-4 py-10">

        {/* 헤더 */}
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-gray-800">🍳 레시피 추천</h1>
          <p className="mt-2 text-gray-500 text-sm">재료로 만들 수 있는 레시피를 AI가 추천합니다</p>
          <div className="flex items-center justify-center gap-2 mt-5">
            <StepBadge num={1} label="재료 인식" done />
            <div className="w-8 h-px bg-gray-300" />
            <StepBadge num={2} label="레시피 생성" active />
            <div className="w-8 h-px bg-gray-300" />
            <StepBadge num={3} label="저장" />
          </div>
        </div>

        {/* 재료 표시 */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-600">인식된 재료</span>
            <button
              onClick={() => router.push("/")}
              className="text-xs text-blue-500 hover:underline"
            >
              ← 재료 수정
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {ingredients.length === 0 ? (
              <span className="text-gray-400 text-sm">재료가 없습니다. Step 1로 돌아가주세요.</span>
            ) : (
              ingredients.map((ing) => (
                <span key={ing} className="px-2.5 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">
                  {ing}
                </span>
              ))
            )}
          </div>
          {/* [M-8] 알레르기 정보 표시 */}
          {allergies.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              <span className="text-xs text-red-500 font-semibold self-center">알레르기 제외:</span>
              {allergies.map((a) => (
                <span key={a} className="px-2.5 py-1 bg-red-100 text-red-600 rounded-full text-xs font-medium">
                  {a}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 옵션 패널 */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 mb-4 space-y-4">
          <p className="text-sm font-semibold text-gray-600">옵션 설정</p>

          {/* 인원수 */}
          <div>
            <p className="text-xs text-gray-400 mb-1.5">인원수</p>
            <div className="flex gap-2">
              {SERVINGS_OPTIONS.map(({ label, value }) => (
                <OptionBtn
                  key={value}
                  active={options.servings === value}
                  onClick={() => setOptions((p) => ({ ...p, servings: value }))}
                >
                  {label}
                </OptionBtn>
              ))}
            </div>
          </div>

          {/* 요리 시간 */}
          <div>
            <p className="text-xs text-gray-400 mb-1.5">요리 시간</p>
            <div className="flex gap-2 flex-wrap">
              {TIME_OPTIONS.map(({ label, value }) => (
                <OptionBtn
                  key={label}
                  active={options.maxTime === value}
                  onClick={() => setOptions((p) => ({ ...p, maxTime: value }))}
                >
                  {label}
                </OptionBtn>
              ))}
            </div>
          </div>

          {/* 식단 */}
          <div>
            <p className="text-xs text-gray-400 mb-1.5">식단 (복수 선택)</p>
            <div className="flex gap-2 flex-wrap">
              {DIET_OPTIONS.map((d) => (
                <OptionBtn
                  key={d}
                  active={options.diet.includes(d)}
                  onClick={() => toggleDiet(d)}
                >
                  {d}
                </OptionBtn>
              ))}
            </div>
          </div>

          {/* 추천 개수 */}
          <div>
            <p className="text-xs text-gray-400 mb-1.5">추천 개수</p>
            <div className="flex gap-2">
              {COUNT_OPTIONS.map(({ label, value }) => (
                <OptionBtn
                  key={value}
                  active={options.count === value}
                  onClick={() => setOptions((p) => ({ ...p, count: value }))}
                >
                  {label}
                </OptionBtn>
              ))}
            </div>
          </div>
        </div>

        {/* 생성 버튼 / 취소 버튼 */}
        <div className="flex gap-2">
          <button
            onClick={handleGenerate}
            disabled={isGenerating || ingredients.length === 0}
            className="flex-1 py-3 rounded-xl font-semibold text-white transition-all
              bg-orange-500 hover:bg-orange-600 active:scale-95
              disabled:bg-gray-300 disabled:cursor-not-allowed disabled:scale-100"
          >
            {isGenerating ? (
              <span className="flex items-center justify-center gap-2">
                <Spinner />
                AI가 레시피를 생성하는 중...
              </span>
            ) : status === "done" ? (
              "다시 생성하기"
            ) : (
              "레시피 생성하기"
            )}
          </button>
          {isGenerating && (
            <button
              onClick={() => { abortRef.current?.abort(); setStatus("idle"); setStreamText(""); }}
              className="px-4 py-3 rounded-xl font-semibold text-gray-600 bg-gray-100 hover:bg-gray-200 transition-all shrink-0"
              aria-label="레시피 생성 취소"
            >
              취소
            </button>
          )}
        </div>

        {/* 에러 */}
        {status === "error" && (
          <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 text-red-600 text-sm flex items-start gap-2">
            <span>⚠️</span>
            <div>
              <p>{errorMsg}</p>
              <button onClick={handleGenerate} className="mt-1 text-red-500 underline text-xs">
                다시 시도하기
              </button>
            </div>
          </div>
        )}

        {/* 스트리밍 중 표시 */}
        {isGenerating && (
          <div className="mt-4 bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs text-gray-400 flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" aria-hidden="true" />
                레시피를 구성하고 있어요...
              </p>
              <span className="text-xs text-gray-300">(예상 30~60초)</span>
            </div>
            {streamText && (
              <pre className="text-xs text-gray-500 whitespace-pre-wrap font-mono max-h-40 overflow-y-auto">
                {streamText}
              </pre>
            )}
          </div>
        )}

        {/* 레시피 카드 목록 */}
        {status === "done" && recipes.length > 0 && (
          <div className="mt-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-700">추천 레시피 {recipes.length}개</h2>
              <button
                onClick={() => router.push("/my-recipes")}
                className="text-xs text-emerald-600 hover:underline"
              >
                내 레시피북 보기 →
              </button>
            </div>
            {recipes.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                ownedIngredients={ingredients}
                onSave={handleSave}
                saved={savedIds.has(recipe.id)}
              />
            ))}

            {/* Step 3 이동 — 저장한 레시피가 있을 때 강조 버튼 */}
            {savedIds.size > 0 && (
              <button
                onClick={() => router.push("/my-recipes")}
                className="w-full py-3 rounded-xl font-semibold text-white
                  bg-emerald-500 hover:bg-emerald-600 active:scale-95 transition-all
                  flex items-center justify-center gap-2"
              >
                <span aria-hidden="true">📚</span> 레시피북에서 보기
                <span aria-hidden="true">→</span>
              </button>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

// ── 서브 컴포넌트 ─────────────────────────────────────────────────────────────
function OptionBtn({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all
        ${active
          ? "bg-orange-500 text-white"
          : "bg-gray-100 text-gray-600 hover:bg-gray-200"
        }`}
    >
      {children}
    </button>
  );
}

function StepBadge({ num, label, active, done }: { num: number; label: string; active?: boolean; done?: boolean }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
          ${done ? "bg-emerald-500 text-white" : active ? "bg-orange-500 text-white" : "bg-gray-200 text-gray-400"}`}
      >
        {done ? "✓" : num}
      </div>
      <span className={`text-xs ${done ? "text-emerald-600" : active ? "text-orange-600 font-semibold" : "text-gray-400"}`}>
        {label}
      </span>
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
