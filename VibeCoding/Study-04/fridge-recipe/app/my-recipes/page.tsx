"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useLocalStorage } from "@/lib/useLocalStorage";
import { SavedRecipe, UserProfile, LS_RECIPES, LS_PROFILE } from "@/lib/types";

type SortKey = "savedAt" | "rating" | "time";
type FilterKey = "all" | "favorite" | "쉬움" | "보통" | "어려움";

function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return "방금 전";
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}일 전`;
  return `${Math.floor(diff / 604800)}주 전`;
}

function StarRow({ rating }: { rating: number | null }) {
  return (
    <span className="text-yellow-400 text-sm">
      {rating ? "★".repeat(rating) + "☆".repeat(5 - rating) : <span className="text-gray-300 text-xs">미평가</span>}
    </span>
  );
}

export default function MyRecipesPage() {
  const router = useRouter();
  const [recipes] = useLocalStorage<SavedRecipe[]>(LS_RECIPES, []);
  const [profile] = useLocalStorage<UserProfile | null>(LS_PROFILE, null);

  const [sort, setSort] = useState<SortKey>("savedAt");
  const [filter, setFilter] = useState<FilterKey>("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    let list = [...recipes];
    // 필터
    if (filter === "favorite") list = list.filter((r) => r.isFavorite);
    else if (filter !== "all") list = list.filter((r) => r.difficulty === filter);
    // 검색
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      list = list.filter(
        (r) =>
          r.title.toLowerCase().includes(q) ||
          [...r.usedIngredients, ...r.extraIngredients].some((i) => i.toLowerCase().includes(q))
      );
    }
    // 정렬
    list.sort((a, b) => {
      if (sort === "savedAt") return new Date(b.savedAt).getTime() - new Date(a.savedAt).getTime();
      if (sort === "rating") return (b.rating ?? 0) - (a.rating ?? 0);
      if (sort === "time") return a.time - b.time;
      return 0;
    });
    return list;
  }, [recipes, filter, sort, search]);

  const FILTER_OPTS: { label: string; key: FilterKey }[] = [
    { label: "전체", key: "all" },
    { label: "즐겨찾기 ★", key: "favorite" },
    { label: "쉬움", key: "쉬움" },
    { label: "보통", key: "보통" },
    { label: "어려움", key: "어려움" },
  ];

  return (
    <main className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50">
      <div className="max-w-xl mx-auto px-4 py-10">
        {/* 헤더 */}
        <div className="flex items-center gap-3 mb-2">
          <button onClick={() => router.push("/")} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">←</button>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">
              {profile ? `${profile.nickname}님의 레시피북` : "📚 레시피북"}
            </h1>
            <p className="text-gray-400 text-sm">저장된 레시피 {recipes.length}개</p>
          </div>
          {profile && (
            <button onClick={() => router.push("/profile")}
              style={{ backgroundColor: profile.avatarColor }}
              className="ml-auto w-10 h-10 rounded-full flex items-center justify-center text-xl shadow-sm">
              {profile.avatar}
            </button>
          )}
        </div>

        {/* 필터 */}
        <div className="flex gap-2 flex-wrap mt-5 mb-3">
          {FILTER_OPTS.map(({ label, key }) => (
            <button key={key} onClick={() => setFilter(key)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all
                ${filter === key ? "bg-emerald-500 text-white" : "bg-white text-gray-600 border border-gray-200 hover:border-emerald-300"}`}>
              {label}
            </button>
          ))}
        </div>

        {/* 정렬 + 검색 */}
        <div className="flex gap-2 mb-5">
          <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)}
            className="px-3 py-2 rounded-lg border border-gray-200 bg-white text-sm text-gray-600
              focus:outline-none focus:border-emerald-400">
            <option value="savedAt">최신순</option>
            <option value="rating">별점순</option>
            <option value="time">시간순</option>
          </select>
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="🔍 요리명 또는 재료 검색..."
            className="flex-1 px-3 py-2 rounded-lg border border-gray-200 bg-white text-sm
              focus:outline-none focus:border-emerald-400" />
        </div>

        {/* 목록 */}
        {filtered.length === 0 ? (
          recipes.length === 0 ? (
            /* 전체 레시피가 없는 경우 — 친근한 Empty State */
            <div className="flex flex-col items-center py-20 text-center">
              <span className="text-6xl mb-4" aria-hidden="true">🧊</span>
              <p className="text-gray-700 font-semibold text-base mb-1">아직 저장된 레시피가 없어요</p>
              <p className="text-gray-400 text-sm mb-6">냉장고를 찍어 AI 레시피를 만들어보세요!</p>
              <button
                onClick={() => router.push("/")}
                className="px-6 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl text-sm font-semibold active:scale-95 transition-all"
              >
                냉장고 사진 찍으러 가기
              </button>
            </div>
          ) : (
            /* 검색/필터 결과 없음 */
            <div className="flex flex-col items-center py-20 text-center">
              <span className="text-5xl mb-4" aria-hidden="true">🔍</span>
              <p className="text-gray-700 font-semibold text-base mb-1">검색 결과가 없어요</p>
              <p className="text-gray-400 text-sm mb-4">다른 키워드나 필터를 사용해보세요.</p>
              <button
                onClick={() => { setSearch(""); setFilter("all"); }}
                className="px-5 py-2 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-xl text-sm font-medium transition-all"
              >
                필터 초기화
              </button>
            </div>
          )
        ) : (
          <div className="grid grid-cols-2 gap-3">
            {filtered.map((r) => (
              <button
                key={r.id}
                onClick={() => router.push(`/my-recipes/${r.id}`)}
                aria-label={`${r.title} 레시피 보기${r.isFavorite ? ", 즐겨찾기" : ""}`}
                className="bg-white rounded-2xl p-3 shadow-sm border border-gray-100 text-left
                  hover:shadow-md hover:border-emerald-200 active:scale-95 transition-all">
                {/* 썸네일 or 이모지 */}
                <div className="w-full h-24 rounded-xl mb-2 overflow-hidden bg-orange-50 flex items-center justify-center">
                  {r.thumbnail
                    ? <img src={r.thumbnail} alt="" className="w-full h-full object-cover" />
                    : <span className="text-4xl" aria-hidden="true">🍳</span>}
                </div>
                <p className="font-semibold text-gray-800 text-sm leading-tight line-clamp-2 mb-1">{r.title}</p>
                <p className="text-xs text-gray-400">⏱ {r.time}분</p>
                <div className="mt-1"><StarRow rating={r.rating} /></div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-gray-300">{timeAgo(r.savedAt)}</span>
                  {r.isFavorite && <span className="text-yellow-400 text-sm" aria-label="즐겨찾기">★</span>}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
