"use client";

export interface Recipe {
  id: string;
  title: string;
  time: number;
  difficulty: "쉬움" | "보통" | "어려움";
  servings: number;
  usedIngredients: string[];
  extraIngredients: string[];
  steps: string[];
}

interface Props {
  recipe: Recipe;
  ownedIngredients: string[];
  onSave: (recipe: Recipe) => void;
  saved: boolean;
}

const DIFFICULTY_COLOR = {
  쉬움: "text-emerald-600 bg-emerald-50",
  보통: "text-yellow-600 bg-yellow-50",
  어려움: "text-red-600 bg-red-50",
};

export default function RecipeCard({ recipe, ownedIngredients, onSave, saved }: Props) {
  // [m-2] owned Set을 usedIngredients 색 구분에 실제 활용
  const owned = new Set(ownedIngredients.map((i) => i.trim().toLowerCase()));

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      {/* 카드 헤더 */}
      <div className="bg-gradient-to-r from-orange-50 to-amber-50 px-5 py-4 border-b border-gray-100">
        <h3 className="text-lg font-bold text-gray-800">🍳 {recipe.title}</h3>
        <div className="flex items-center gap-3 mt-2 text-sm">
          <span className="flex items-center gap-1 text-gray-500">
            ⏱ {recipe.time}분
          </span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${DIFFICULTY_COLOR[recipe.difficulty] ?? "text-gray-600 bg-gray-100"}`}>
            {recipe.difficulty}
          </span>
          <span className="flex items-center gap-1 text-gray-500">
            👥 {recipe.servings}인분
          </span>
        </div>
      </div>

      <div className="px-5 py-4 space-y-4">
        {/* 재료 */}
        <div>
          <p className="text-sm font-semibold text-gray-600 mb-2">재료</p>
          <div className="flex flex-wrap gap-1.5">
            {recipe.usedIngredients.map((ing) => {
              // [m-2] 실제 보유 여부에 따라 색상을 달리 적용
              const isOwned = owned.has(ing.trim().toLowerCase());
              return (
                <span
                  key={ing}
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium
                    ${isOwned
                      ? "bg-emerald-100 text-emerald-700 border border-emerald-200"
                      : "bg-orange-100 text-orange-600 border border-orange-200"
                    }`}
                >
                  <span aria-hidden="true">{isOwned ? "✓" : "✗"}</span>
                  <span className="sr-only">{isOwned ? "보유" : "미보유"}</span>
                  {ing}
                </span>
              );
            })}
            {recipe.extraIngredients.map((ing) => (
              <span
                key={ing}
                className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium
                  bg-orange-100 text-orange-600 border border-orange-200"
              >
                + {ing}
              </span>
            ))}
          </div>
          {(recipe.extraIngredients.length > 0 || recipe.usedIngredients.some((i) => !owned.has(i.trim().toLowerCase()))) && (
            <p className="text-xs text-gray-400 mt-1.5">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 mr-1" aria-hidden="true" />보유
              <span className="inline-block w-2 h-2 rounded-full bg-orange-400 ml-3 mr-1" aria-hidden="true" />미보유
              <span className="inline-block w-2 h-2 rounded-full bg-orange-300 ml-3 mr-1" aria-hidden="true" />추가 필요
            </p>
          )}
        </div>

        {/* 조리법 */}
        <div>
          <p className="text-sm font-semibold text-gray-600 mb-2">조리법</p>
          <ol className="space-y-2">
            {recipe.steps.map((step, idx) => (
              <li key={idx} className="flex gap-3 text-sm text-gray-700">
                <span className="shrink-0 w-5 h-5 rounded-full bg-blue-500 text-white text-xs
                  flex items-center justify-center font-bold mt-0.5">
                  {idx + 1}
                </span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* 저장 버튼 */}
        <button
          onClick={() => onSave(recipe)}
          disabled={saved}
          className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-all
            ${saved
              ? "bg-gray-100 text-gray-400 cursor-default"
              : "bg-blue-500 hover:bg-blue-600 active:scale-95 text-white"
            }`}
        >
          {saved ? "✓ 저장됨" : "저장하기"}
        </button>
      </div>
    </div>
  );
}
