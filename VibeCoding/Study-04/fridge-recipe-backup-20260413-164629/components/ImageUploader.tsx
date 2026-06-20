"use client";

import { useCallback, useRef, useState } from "react";
import Image from "next/image";

interface Props {
  onImageSelect: (dataUrl: string) => void;
  imageDataUrl: string | null;
}

const MAX_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_DIM = 1024; // 최대 해상도 (px)
const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];

export default function ImageUploader({ onImageSelect, imageDataUrl }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [sizeError, setSizeError] = useState<string | null>(null);

  const processFile = useCallback(
    (file: File) => {
      setSizeError(null);
      if (!ACCEPTED.includes(file.type)) {
        setSizeError("JPG, PNG, WEBP 형식만 지원합니다.");
        return;
      }
      if (file.size > MAX_SIZE) {
        setSizeError("파일 크기는 10MB 이하여야 합니다.");
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const original = e.target?.result as string;
        // [C-5] .catch로 Promise 누수 방지
        resizeImage(original, MAX_DIM)
          .then(onImageSelect)
          .catch((err: unknown) => {
            console.error("이미지 리사이즈 실패:", err);
            setSizeError(err instanceof Error ? err.message : "이미지를 처리할 수 없습니다.");
          });
      };
      reader.readAsDataURL(file);
    },
    [onImageSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) processFile(file);
    },
    [processFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    e.target.value = "";
  };

  return (
    <div>
      {imageDataUrl ? (
        /* 미리보기 */
        <div className="relative rounded-2xl overflow-hidden border-2 border-blue-200 shadow-md">
          <div className="relative w-full h-64">
            <Image src={imageDataUrl} alt="업로드된 냉장고 사진" fill className="object-contain bg-gray-50" />
          </div>
          <button
            onClick={() => inputRef.current?.click()}
            className="absolute bottom-3 right-3 bg-white/90 hover:bg-white text-gray-700
              text-xs font-medium px-3 py-1.5 rounded-full shadow transition-all"
          >
            📷 사진 변경
          </button>
        </div>
      ) : (
        /* 업로드 영역 */
        <div
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={`cursor-pointer rounded-2xl border-2 border-dashed transition-all
            flex flex-col items-center justify-center h-56 gap-3
            ${dragging
              ? "border-blue-400 bg-blue-50 scale-[1.01]"
              : "border-gray-300 bg-white hover:border-blue-300 hover:bg-blue-50/50"
            }`}
        >
          <span className="text-5xl">📷</span>
          <div className="text-center">
            <p className="text-gray-600 font-medium">사진을 드래그하거나 클릭하여 업로드</p>
            <p className="text-gray-400 text-sm mt-1">JPG, PNG, WEBP · 최대 10MB</p>
          </div>
        </div>
      )}

      {sizeError && (
        <p className="mt-2 text-red-500 text-sm text-center">⚠️ {sizeError}</p>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        capture="environment"
        onChange={handleChange}
        className="hidden"
      />
    </div>
  );
}

// [C-5] onerror 핸들러 추가 + getContext null 체크로 Promise 누수 방지
function resizeImage(dataUrl: string, maxDim: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new window.Image();
    img.onload = () => {
      let { width, height } = img;
      if (width <= maxDim && height <= maxDim) { resolve(dataUrl); return; }
      const scale = Math.min(maxDim / width, maxDim / height);
      width = Math.round(width * scale);
      height = Math.round(height * scale);
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      if (!ctx) { resolve(dataUrl); return; }
      ctx.drawImage(img, 0, 0, width, height);
      resolve(canvas.toDataURL("image/jpeg", 0.85));
    };
    img.onerror = () => reject(new Error("이미지를 불러올 수 없습니다."));
    img.src = dataUrl;
  });
}
