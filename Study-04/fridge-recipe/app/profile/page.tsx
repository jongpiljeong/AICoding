"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useLocalStorage } from "@/lib/useLocalStorage";
import { UserProfile, LS_PROFILE } from "@/lib/types";
import Toast from "@/components/Toast";
// [m-6] 공통 상수에서 import
import { DIET_OPTIONS } from "@/lib/constants";

const AVATARS = ["👨‍🍳", "👩‍🍳", "🧑‍🍳", "🍽️", "🥘", "🫕"];
const COLORS = ["#FEE2E2", "#FEF3C7", "#D1FAE5", "#DBEAFE", "#EDE9FE", "#FCE7F3"];

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile, hydrated] = useLocalStorage<UserProfile | null>(LS_PROFILE, null);
  const [toast, setToast] = useState<string | null>(null);

  // [M-5] 초기값은 항상 빈 값 — hydration 후 useEffect에서 profile 동기화
  const [nickname, setNickname] = useState("");
  const [avatar, setAvatar] = useState(AVATARS[0]);
  const [avatarColor, setAvatarColor] = useState(COLORS[0]);
  const [diet, setDiet] = useState<string[]>(["일반"]);
  const [allergyInput, setAllergyInput] = useState("");
  const [allergies, setAllergies] = useState<string[]>([]);

  // [M-5] hydration 완료 후 profile이 있으면 폼 동기화
  useEffect(() => {
    if (hydrated && profile) {
      setNickname(profile.nickname ?? "");
      setAvatar(profile.avatar ?? AVATARS[0]);
      setAvatarColor(profile.avatarColor ?? COLORS[0]);
      setDiet(profile.dietPreferences ?? ["일반"]);
      setAllergies(profile.allergies ?? []);
    }
  }, [hydrated]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleDiet = (d: string) =>
    setDiet((p) => (p.includes(d) ? p.filter((x) => x !== d) : [...p, d]));

  const addAllergy = () => {
    const t = allergyInput.trim();
    if (t && !allergies.includes(t)) { setAllergies((p) => [...p, t]); setAllergyInput(""); }
  };

  const handleSave = () => {
    const now = new Date().toISOString();
    setProfile({
      id: profile?.id ?? crypto.randomUUID(),
      nickname: nickname.trim() || "셰프",
      avatar,
      avatarColor,
      dietPreferences: diet,
      allergies,
      createdAt: profile?.createdAt ?? now,
      updatedAt: now,
    });
    setToast("프로필이 저장되었습니다.");
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50">
      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
      <div className="max-w-md mx-auto px-4 py-10">
        <div className="flex items-center gap-3 mb-8">
          <button onClick={() => router.back()} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">←</button>
          <h1 className="text-2xl font-bold text-gray-800">프로필 설정</h1>
        </div>

        <div className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 space-y-5">
          {/* 아바타 미리보기 */}
          <div className="flex justify-center">
            <div style={{ backgroundColor: avatarColor }}
              className="w-20 h-20 rounded-full flex items-center justify-center text-4xl shadow-md">
              {avatar}
            </div>
          </div>

          {/* 닉네임 */}
          <div>
            <label className="text-sm font-semibold text-gray-600 mb-1 block">닉네임</label>
            <input type="text" value={nickname} onChange={(e) => setNickname(e.target.value)}
              placeholder="예: 홍길동 셰프" maxLength={20}
              className="w-full px-3 py-2 rounded-lg border border-gray-200
                focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-200 text-sm" />
          </div>

          {/* 아바타 선택 */}
          <div>
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
                    ${avatar === a ? "ring-2 ring-blue-400 scale-110" : "hover:scale-105"}`}>
                  {a}
                </button>
              ))}
            </div>
          </div>

          {/* 식단 선호도 */}
          <div>
            <label className="text-sm font-semibold text-gray-600 mb-2 block">식단 선호도</label>
            <div className="flex flex-wrap gap-2">
              {DIET_OPTIONS.map((d) => (
                <button key={d} onClick={() => toggleDiet(d)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all
                    ${diet.includes(d) ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* 알레르기 */}
          <div>
            <label className="text-sm font-semibold text-gray-600 mb-2 block">알레르기 재료</label>
            <div className="flex gap-2">
              <input type="text" value={allergyInput} onChange={(e) => setAllergyInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addAllergy()}
                placeholder="견과류, 유제품... (Enter)"
                className="flex-1 px-3 py-2 rounded-lg border border-gray-200
                  focus:outline-none focus:border-blue-400 text-sm" />
              <button onClick={addAllergy} className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm">추가</button>
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
        </div>

        <button onClick={handleSave}
          className="mt-5 w-full py-3 rounded-xl font-semibold text-white bg-blue-500 hover:bg-blue-600 active:scale-95 transition-all">
          저장하기
        </button>
        <button onClick={() => router.push("/my-recipes")}
          className="mt-3 w-full py-3 rounded-xl font-semibold text-emerald-600 bg-emerald-50 hover:bg-emerald-100 transition-all">
          📚 내 레시피북 보기
        </button>
      </div>
    </main>
  );
}
