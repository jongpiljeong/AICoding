import { NextRequest } from "next/server";

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
const BASE_URL = "https://openrouter.ai/api/v1";
const MODEL = "nvidia/nemotron-3-super-120b-a12b:free";

function buildPrompt(
  ingredients: string[],
  servings: number,
  maxTime: number | null,
  diet: string[],
  count: number,
  allergies: string[]
): string {
  const timeStr = maxTime ? `${maxTime}분 이내` : "제한 없음";
  // [M-8] 알레르기 정보를 프롬프트에 반영
  const allergyStr =
    allergies.length > 0
      ? `\n알레르기 제외 재료: ${allergies.join(", ")} (이 재료들이 포함된 레시피는 절대 추천하지 마세요.)`
      : "";
  return `다음 재료로 만들 수 있는 한국어 레시피를 ${count}개 추천해주세요.

재료: ${ingredients.join(", ")}
인원: ${servings}인분
요리 시간: ${timeStr}
식단: ${diet.join(", ")}${allergyStr}

반드시 아래 JSON 형식으로만 응답하세요. 설명이나 마크다운 없이 JSON만 출력하세요.
{
  "recipes": [
    {
      "title": "요리명",
      "time": 예상시간(숫자, 분 단위),
      "difficulty": "쉬움 또는 보통 또는 어려움",
      "servings": ${servings},
      "usedIngredients": ["제공된 재료 중 사용하는 것만"],
      "extraIngredients": ["추가로 필요한 재료"],
      "steps": ["1단계 설명", "2단계 설명", ...]
    }
  ]
}`;
}

export async function POST(req: NextRequest) {
  if (!OPENROUTER_API_KEY) {
    return new Response(JSON.stringify({ error: "API 키가 설정되지 않았습니다." }), { status: 500 });
  }

  // [C-2] req.json() 파싱 try/catch + ingredients 검증
  let ingredients: string[];
  let options: {
    servings?: number;
    maxTime?: number | null;
    diet?: string[];
    count?: number;
    allergies?: string[];
  };

  try {
    const body = await req.json();
    ingredients = body.ingredients;
    options = body.options ?? {};
  } catch {
    return new Response(JSON.stringify({ error: "요청 본문을 파싱할 수 없습니다." }), { status: 400 });
  }

  // [C-2] Array.isArray 검증 + 빈 배열 400 반환
  if (!Array.isArray(ingredients) || ingredients.length === 0) {
    return new Response(JSON.stringify({ error: "재료 목록이 비어 있거나 올바르지 않습니다." }), { status: 400 });
  }

  const { servings = 2, maxTime = null, diet = ["일반"], count = 3, allergies = [] } = options;

  const prompt = buildPrompt(ingredients, servings, maxTime, diet, count, allergies);

  // Rate limit 재시도 포함 OpenRouter 호출
  let orResponse: Response | null = null;
  for (let attempt = 1; attempt <= 3; attempt++) {
    const res = await fetch(`${BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${OPENROUTER_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: "user", content: prompt }],
        stream: true,
        max_tokens: 3000,
      }),
      signal: AbortSignal.timeout(90000),
    });

    if (res.status === 429) {
      if (attempt < 3) {
        await new Promise((r) => setTimeout(r, 5000 * attempt));
        continue;
      }
      return new Response(JSON.stringify({ error: "요청이 너무 많습니다. 잠시 후 다시 시도해주세요." }), { status: 429 });
    }

    if (!res.ok) {
      // [C-3] 오류 응답 본문을 읽어 서버 로그에 출력
      const errBody = await res.text().catch(() => "(본문 읽기 실패)");
      console.error(`OpenRouter error [${res.status}]:`, errBody);
      return new Response(JSON.stringify({ error: "레시피 생성 중 오류가 발생했습니다." }), { status: 500 });
    }

    orResponse = res;
    break;
  }

  if (!orResponse?.body) {
    return new Response(JSON.stringify({ error: "스트림을 받을 수 없습니다." }), { status: 500 });
  }

  // OpenRouter SSE → 클라이언트로 텍스트 청크만 추출하여 스트리밍
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();

  const stream = new ReadableStream({
    async start(controller) {
      const reader = orResponse!.body!.getReader();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const data = line.slice(6).trim();
            if (data === "[DONE]") continue;

            try {
              const json = JSON.parse(data);
              const delta = json.choices?.[0]?.delta?.content;
              if (delta) {
                controller.enqueue(encoder.encode(delta));
              }
            } catch {
              // 파싱 불가 라인 무시
            }
          }
        }
      } finally {
        controller.close();
        reader.releaseLock();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Transfer-Encoding": "chunked",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
