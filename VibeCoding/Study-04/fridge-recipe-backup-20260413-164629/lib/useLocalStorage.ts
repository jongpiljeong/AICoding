"use client";

import { useState, useEffect, useCallback } from "react";

// SSR 안전 localStorage 읽기
function readLS<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function writeLS<T>(key: string, value: T): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // localStorage 비활성화 환경 무시
  }
}

export function useLocalStorage<T>(key: string, fallback: T) {
  const [value, setValue] = useState<T>(fallback);
  const [hydrated, setHydrated] = useState(false);

  // 클라이언트 마운트 후 실제 값 로드
  useEffect(() => {
    setValue(readLS(key, fallback));
    setHydrated(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const set = useCallback(
    (next: T | ((prev: T) => T)) => {
      setValue((prev) => {
        const updated = typeof next === "function" ? (next as (p: T) => T)(prev) : next;
        writeLS(key, updated);
        return updated;
      });
    },
    [key]
  );

  return [value, set, hydrated] as const;
}
