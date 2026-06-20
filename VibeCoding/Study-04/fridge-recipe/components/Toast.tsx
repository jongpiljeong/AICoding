"use client";

import { useEffect, useRef } from "react";

interface Props {
  message: string;
  type?: "success" | "error" | "info";
  onClose: () => void;
  duration?: number;
}

const ICONS = { success: "✅", error: "❌", info: "ℹ️" };
const COLORS = {
  success: "bg-emerald-600",
  error: "bg-red-500",
  info: "bg-blue-500",
};

export default function Toast({ message, type = "success", onClose, duration = 2500 }: Props) {
  // onClose를 ref로 고정해 매 렌더마다 타이머가 리셋되는 문제 방지
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    const t = setTimeout(() => onCloseRef.current(), duration);
    return () => clearTimeout(t);
  }, [duration]);

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50
        flex items-center gap-2 px-5 py-3 rounded-xl shadow-lg text-white text-sm font-medium
        animate-[slideUp_0.3s_ease-out] ${COLORS[type]}`}
    >
      <span>{ICONS[type]}</span>
      <span>{message}</span>
    </div>
  );
}
