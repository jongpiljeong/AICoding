"use client";

import { useState, KeyboardEvent } from "react";

interface Ingredient {
  text: string;
  auto: boolean;
}

interface Props {
  ingredients: Ingredient[];
  onAdd: (text: string) => void;
  onRemove: (index: number) => void;
}

export default function IngredientTags({ ingredients, onAdd, onRemove }: Props) {
  const [input, setInput] = useState("");

  const handleAdd = () => {
    const trimmed = input.trim();
    if (!trimmed) return;
    onAdd(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") handleAdd();
  };

  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-gray-700">인식된 재료</h2>
        <span className="text-xs text-gray-400">{ingredients.length}개</span>
      </div>

      {/* 범례 */}
      <div className="flex gap-3 mb-3">
        <span className="flex items-center gap-1 text-xs text-gray-400">
          <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />
          AI 인식
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
          수동 추가
        </span>
      </div>

      {/* 태그 목록 */}
      <div className="flex flex-wrap gap-2 min-h-[40px]">
        {ingredients.map((ing, idx) => (
          <span
            key={`${ing.text}-${idx}`}
            className={`flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium transition-all
              ${ing.auto
                ? "bg-blue-100 text-blue-700 border border-blue-200"
                : "bg-emerald-100 text-emerald-700 border border-emerald-200"
              }`}
          >
            {ing.text}
            <button
              onClick={() => onRemove(idx)}
              className="ml-0.5 hover:opacity-60 transition-opacity leading-none text-base"
              aria-label={`${ing.text} 삭제`}
            >
              ×
            </button>
          </span>
        ))}
        {ingredients.length === 0 && (
          <p className="text-gray-400 text-sm self-center">재료가 없습니다. 직접 추가해보세요.</p>
        )}
      </div>

      {/* 수동 추가 입력 */}
      <div className="flex gap-2 mt-4">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="재료 직접 추가 (Enter)"
          className="flex-1 px-3 py-2 text-sm rounded-lg border border-gray-200
            focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-200 transition-all"
        />
        <button
          onClick={handleAdd}
          disabled={!input.trim()}
          className="px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-600
            text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          + 추가
        </button>
      </div>
    </div>
  );
}
