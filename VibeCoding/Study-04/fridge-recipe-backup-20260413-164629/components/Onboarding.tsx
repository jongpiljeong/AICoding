"use client";

import { useEffect, useState } from "react";
import { UserProfile } from "@/lib/types";
// [m-6] 공통 상수에서 import
import { DIET_OPTIONS } from "@/lib/constants";

const AVATARS = ["👨‍🍳", "👩‍🍳", "🧑‍🍳", "🍽️", "🥘", "🫕"];
const COLORS = ["#FEE2E2", "#FEF3C7", "#D1FAE5", "#DBEAFE", "#EDE9FE", "#FCE7F3"];

interface Props {
  onSave: (profile: UserProfile) => void;
  onSkip: () => void;
}

export default function Onboarding({ onSave, onSkip }: Props) {
  const [nickname, setNickname] = useState("");
  const [avatar, setAvatar] = useState(AVATARS[0]);
  const [avatarColor, setAvatarColor] = useState(COLORS[0]);
  const [diet, setDiet] = useState<string[]>(["일반"]);
  const [allergyInput, setAllergyInput] = useState("");
  const [allergies, setAllergies] = useState<string[]>([]);

  // ESC 키로 온보딩 닫기
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onSkip();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onSkip]);

  const toggleDiet = (d: string) =>
    setDiet((prev) => (prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]));

  const addAllergy = () => {
    const t = allergyInput.trim();
    if (t && !allergies.includes(t)) {
      setAllergies((prev) => [...prev, t]);
      setAllergyInput("");
    }
  };

  const handleSave = () => {
    const now = new Date().toISOString();
    onSave({
      id: crypto.randomUUID(),
      nickname: nickname.trim() || "셰프",
      avatar,
      avatarColor,
      dietPreferences: diet,
      allergies,
      createdAt: now,
      updatedAt: now,
    });
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-title"
    >
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md p-6 animate-[fadeIn_0.2s_ease-out]">
        <div className="text-center mb-6">
          <div className="text-4xl mb-2" aria-hidden="true">👋</div>
          <h2 id="onboarding-title" className="text-xl font-bold text-gray-800">환영합니다!</h2>
          <p className="text-gray-500 text-sm mt-1">프로필을 설정하면 더 맞춤화된 레시피를 추천받을 수 있어요.</p>
        </div>

        {/* 닉네임 */}
        <div className="mb-4">
          <label className="text-sm font-semibold text-gray-600 mb-1 block">닉네임</label>
          <input
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder="예: 홍길동 셰프"
            maxLength={20}
            className="w-full px-3 py-2 rounded-lg border border-gray-200
              focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-200 text-sm"
          />
        </div>

        {/* 아바타 */}
        <div className="mb-4">
          <label className="text-sm font-semibold text-gray-600 mb-2 block">아바타</label>
          <div className="flex gap-2 flex-wrap">
            {AVATARS.map((a, i) => (
              <button
                key={a}
                onClick={() => { setAvatar(a); setAvatarColor(COLORS[i % COLORS.length]); }}
                style={{ backgroundColor: avatar === a ? avatarColor : "#F3F4F6" }}
                aria-label={`아바타 ${a} 선택${avatar === a ? " (현재 선택됨)" : ""}`}
                aria-pressed={avatar === a}
                className={`w-10 h-10 rounded-full text-xl flex items-center justify-center transition-all
                  ${avatar === a ? "ring-2 ring-blue-400 scale-110" : "hover:scale-105"}`}
              >
                {a}
              </button>
            ))}
          </div>
        </div>

        {/* 식단 선호도 */}
        <div className="mb-4">
          <label className="text-sm font-semibold text-gray-600 mb-2 block">식단 선호도</label>
          <div className="flex flex-wrap gap-2">
            {DIET_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => toggleDiet(d)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                  ${diet.includes(d) ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>

        {/* 알레르기 */}
        <div className="mb-6">
          <label className="text-sm font-semibold text-gray-600 mb-2 block">알레르기 재료</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={allergyInput}
              onChange={(e) => setAllergyInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addAllergy()}
              placeholder="예: 견과류, 유제품 (Enter)"
              className="flex-1 px-3 py-2 rounded-lg border border-gray-200
                focus:outline-none focus:border-blue-400 text-sm"
            />
            <button
              onClick={addAllergy}
              className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm"
            >
              추가
            </button>
          </div>
          {allergies.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {allergies.map((a) => (
                <span key={a} className="flex items-center gap-1 px-2.5 py-1 bg-red-100 text-red-600 rounded-full text-xs">
                  {a}
                  <button onClick={() => setAllergies((p) => p.filter((x) => x !== a))} className="hover:opacity-60">×</button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 버튼 */}
        <div className="flex gap-3">
          <button
            onClick={onSkip}
            className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-500 text-sm font-medium hover:bg-gray-50"
          >
            건너뛰기
          </button>
          <button
            onClick={handleSave}
            className="flex-1 py-2.5 rounded-xl bg-blue-500 hover:bg-blue-600 text-white text-sm font-semibold"
          >
            프로필 만들기
          </button>
        </div>
      </div>
    </div>
  );
}
