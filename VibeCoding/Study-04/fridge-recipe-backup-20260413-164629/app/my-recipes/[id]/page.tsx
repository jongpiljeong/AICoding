"use client";

import { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useLocalStorage } from "@/lib/useLocalStorage";
import { SavedRecipe, LS_RECIPES } from "@/lib/types";
import Toast from "@/components/Toast";

const DIFFICULTY_COLOR: Record<string, string> = {
  쉬움: "text-emerald-600 bg-emerald-50",
  보통: "text-yellow-600 bg-yellow-50",
  어려움: "text-red-600 bg-red-50",
};

export default function RecipeDetailPage() {
  const router = useRouter();
  const { id } = useParams<{ id: string }>();
  const [recipes, setRecipes] = useLocalStorage<SavedRecipe[]>(LS_RECIPES, []);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" | "info" } | null>(null);

  const recipe = recipes.find((r) => r.id === id);

  const [memo, setMemo] = useState(recipe?.memo ?? "");
  const [memoSaved, setMemoSaved] = useState(false);

  useEffect(() => {
    if (recipe) setMemo(recipe.memo);
  }, [recipe?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!recipe) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-400 mb-4">레시피를 찾을 수 없습니다.</p>
          <button onClick={() => router.push("/my-recipes")}
            className="text-blue-500 underline text-sm">레시피북으로 돌아가기</button>
        </div>
      </main>
    );
  }

  const update = (patch: Partial<SavedRecipe>) =>
    setRecipes((prev) => prev.map((r) => (r.id === id ? { ...r, ...patch } : r)));

  const handleRating = (star: number) => {
    update({ rating: star });
    setToast({ message: `별점 ${star}점 저장!`, type: "success" });
  };

  const handleFavorite = () => {
    const next = !recipe.isFavorite;
    update({ isFavorite: next });
    setToast({ message: next ? "즐겨찾기 추가!" : "즐겨찾기 해제", type: "info" });
  };

  const handleMemoSave = () => {
    update({ memo });
    setMemoSaved(true);
    setToast({ message: "메모 저장 완료!", type: "success" });
    setTimeout(() => setMemoSaved(false), 2000);
  };

  const handleDelete = () => {
    if (!confirm(`"${recipe.title}"을(를) 삭제할까요?`)) return;
    setRecipes((prev) => prev.filter((r) => r.id !== id));
    router.push("/my-recipes");
  };

  const handleRecommend = () => {
    // [M-2] try/catch로 손상된 데이터 대비
    try {
      sessionStorage.setItem("fridgeIngredients", JSON.stringify(recipe.sourceIngredients));
    } catch {
      // sessionStorage 저장 실패 시에도 페이지 이동은 허용
    }
    router.push("/recipe");
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      <div className="max-w-xl mx-auto px-4 py-10">
        {/* 헤더 */}
        <div className="flex items-center justify-between mb-6">
          <button
            onClick={() => router.push("/my-recipes")}
            aria-label="내 레시피북으로 돌아가기"
            className="flex items-center gap-1 text-gray-400 hover:text-gray-700 text-sm font-medium transition-colors"
          >
            <span aria-hidden="true" className="text-xl leading-none">←</span>
            <span>내 레시피로</span>
          </button>
          <div className="flex gap-2">
            {/* 즐겨찾기 */}
            <button
              onClick={handleFavorite}
              aria-label={recipe.isFavorite ? "즐겨찾기 해제" : "즐겨찾기 추가"}
              aria-pressed={recipe.isFavorite}
              className={`w-10 h-10 rounded-full flex items-center justify-center text-xl transition-all
                ${recipe.isFavorite ? "bg-yellow-100 text-yellow-500" : "bg-gray-100 text-gray-300 hover:text-yellow-400"}`}>
              ★
            </button>
            {/* 삭제 */}
            <button
              onClick={handleDelete}
              aria-label="이 레시피 삭제"
              className="w-10 h-10 rounded-full bg-red-50 text-red-400 hover:bg-red-100 flex items-center justify-center text-sm transition-all">
              <span aria-hidden="true">🗑</span>
            </button>
          </div>
        </div>

        {/* 썸네일 */}
        {recipe.thumbnail && (
          <div className="w-full h-48 rounded-2xl overflow-hidden mb-4 shadow-sm">
            <img src={recipe.thumbnail} alt="냉장고 사진" className="w-full h-full object-cover" />
          </div>
        )}

        {/* 레시피 헤더 */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-4">
          <div className="bg-gradient-to-r from-orange-50 to-amber-50 px-5 py-4 border-b border-gray-100">
            <h2 className="text-xl font-bold text-gray-800">🍳 {recipe.title}</h2>
            <div className="flex items-center gap-3 mt-2 text-sm">
              <span className="text-gray-500">⏱ {recipe.time}분</span>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${DIFFICULTY_COLOR[recipe.difficulty] ?? "text-gray-600 bg-gray-100"}`}>
                {recipe.difficulty}
              </span>
              <span className="text-gray-500">👥 {recipe.servings}인분</span>
            </div>
          </div>

          <div className="px-5 py-4 space-y-4">
            {/* 재료 */}
            <div>
              <p className="text-sm font-semibold text-gray-600 mb-2">재료</p>
              <div className="flex flex-wrap gap-1.5">
                {recipe.usedIngredients.map((i) => (
                  <span key={i} className="px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700 border border-emerald-200">✓ {i}</span>
                ))}
                {recipe.extraIngredients.map((i) => (
                  <span key={i} className="px-2.5 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-600 border border-orange-200">+ {i}</span>
                ))}
              </div>
            </div>

            {/* 조리법 */}
            <div>
              <p className="text-sm font-semibold text-gray-600 mb-2">조리법</p>
              <ol className="space-y-2">
                {recipe.steps.map((step, i) => (
                  <li key={i} className="flex gap-3 text-sm text-gray-700">
                    <span className="shrink-0 w-5 h-5 rounded-full bg-blue-500 text-white text-xs flex items-center justify-center font-bold mt-0.5">{i + 1}</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>

        {/* 별점 */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 px-5 py-4 mb-4">
          <p className="text-sm font-semibold text-gray-600 mb-3">별점</p>
          <div className="flex gap-2" role="group" aria-label="별점 선택">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => handleRating(star)}
                aria-label={`별점 ${star}점`}
                aria-pressed={(recipe.rating ?? 0) >= star}
                className={`text-3xl transition-all hover:scale-110 active:scale-95
                  ${(recipe.rating ?? 0) >= star ? "text-yellow-400" : "text-gray-200"}`}>
                ★
              </button>
            ))}
            {recipe.rating && <span className="self-center text-sm text-gray-400 ml-1">{recipe.rating}점</span>}
          </div>
        </div>

        {/* 메모 */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 px-5 py-4 mb-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-semibold text-gray-600">메모</p>
            <span className="text-xs text-gray-300">{memo.length}/500</span>
          </div>
          <textarea
            value={memo}
            onChange={(e) => { if (e.target.value.length <= 500) { setMemo(e.target.value); setMemoSaved(false); } }}
            placeholder="이 레시피에 대한 메모를 남겨보세요..."
            rows={3}
            className="w-full text-sm text-gray-700 resize-none focus:outline-none"
          />
          <button onClick={handleMemoSave}
            className={`mt-2 w-full py-2 rounded-lg text-sm font-medium transition-all
              ${memoSaved ? "bg-emerald-100 text-emerald-600" : "bg-gray-100 hover:bg-gray-200 text-gray-600"}`}>
            {memoSaved ? "✓ 저장됨" : "메모 저장"}
          </button>
        </div>

        {/* 이 재료로 다시 추천받기 */}
        {recipe.sourceIngredients?.length > 0 && (
          <button onClick={handleRecommend}
            className="w-full py-3 rounded-xl font-semibold text-white bg-orange-500 hover:bg-orange-600 active:scale-95 transition-all mb-3">
            🔄 이 재료로 다시 추천받기
          </button>
        )}

        <button onClick={() => router.push("/my-recipes")}
          className="w-full py-3 rounded-xl font-semibold text-emerald-600 bg-emerald-50 hover:bg-emerald-100 transition-all">
          ← 레시피북으로
        </button>
      </div>
    </main>
  );
}
