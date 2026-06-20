/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    // 업로드된 이미지(data URL)는 Next/Image가 그대로 처리
    dangerouslyAllowSVG: false,
  },
};

export default nextConfig;
