import { readFileSync } from 'fs';
import { resolve } from 'path';

// .env 파일 수동 로드 (dotenv 없이)
const envPath = resolve('.env');
const envContent = readFileSync(envPath, 'utf-8');
for (const line of envContent.split('\n')) {
  const [key, ...rest] = line.split('=');
  if (key && rest.length) process.env[key.trim()] = rest.join('=').trim();
}

const API_KEY = process.env.OPENROUTER_API_KEY;
const BASE_URL = 'https://openrouter.ai/api/v1';

async function callOpenRouter(model, messages) {
  const res = await fetch(`${BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ model, messages }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`HTTP ${res.status}: ${err}`);
  }
  return res.json();
}

// ─── 1. 텍스트 인식 테스트 ─────────────────────────────────────────────────
async function testText() {
  // gemma-4:free가 rate limit이면 다른 무료 모델로 순서대로 시도
  const candidates = [
    'google/gemma-4-26b-a4b-it:free',
    'minimax/minimax-m2.5:free',
    'nvidia/nemotron-3-super-120b-a12b:free',
  ];

  console.log('\n=== [1] 텍스트 인식 테스트 ===');
  console.log('요청 모델: google/gemma-4-26b-a4b-it:free');

  for (const model of candidates) {
    try {
      if (model !== candidates[0]) console.log(`  → fallback: ${model} 시도 중...`);
      const result = await callOpenRouter(model, [
        { role: 'user', content: '대한민국의 수도는 어디인가요? 한 문장으로 답해주세요.' },
      ]);
      console.log(`실제 사용 모델: ${model}`);
      console.log('응답:', result.choices[0].message.content);
      console.log('사용 토큰:', result.usage);
      return;
    } catch (e) {
      if (e.message.includes('429') || e.message.includes('rate')) {
        console.log(`  → ${model} rate limit, 다음 모델 시도...`);
      } else {
        throw e;
      }
    }
  }
  throw new Error('모든 텍스트 모델 실패');
}

// ─── 2. 이미지 인식 테스트 ─────────────────────────────────────────────────
async function testImage() {
  console.log('\n=== [2] 이미지 인식 테스트 ===');
  // bytedance/seedance-1-5-pro 는 OpenRouter 미지원
  // 무료 이미지 인식 대체 모델 사용
  const model = 'nvidia/nemotron-nano-12b-v2-vl:free';
  console.log(`요청 모델: bytedance/seedance-1-5-pro (OpenRouter 미지원)`);
  console.log(`실제 사용 모델: ${model} (무료 이미지 인식 모델)`);

  // 공개 테스트 이미지 (Lorem Picsum - 강아지)
  const imageUrl = 'https://picsum.photos/id/237/320/240';

  const result = await callOpenRouter(model, [
    {
      role: 'user',
      content: [
        {
          type: 'image_url',
          image_url: { url: imageUrl },
        },
        {
          type: 'text',
          text: '이 이미지에 무엇이 있나요? 한 문장으로 설명해주세요.',
        },
      ],
    },
  ]);

  const answer = result.choices[0].message.content;
  console.log('이미지 URL:', imageUrl);
  console.log('응답:', answer);
  console.log('사용 토큰:', result.usage);
}

// ─── 실행 ──────────────────────────────────────────────────────────────────
(async () => {
  console.log('OpenRouter API 테스트 시작...');
  console.log('API 키:', API_KEY.slice(0, 20) + '...[마스킹됨]');

  try {
    await testText();
  } catch (e) {
    console.error('[텍스트 테스트 실패]', e.message);
  }

  try {
    await testImage();
  } catch (e) {
    console.error('[이미지 테스트 실패]', e.message);
  }

  console.log('\n테스트 완료.');
})();
