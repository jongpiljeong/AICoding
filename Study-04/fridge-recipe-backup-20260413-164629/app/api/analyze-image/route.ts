import { NextRequest, NextResponse } from "next/server";

const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
const BASE_URL = "https://openrouter.ai/api/v1";
const MODEL = "nvidia/nemotron-nano-12b-v2-vl:free";

export async function POST(req: NextRequest) {
  if (!OPENROUTER_API_KEY) {
    return NextResponse.json({ error: "API 키가 설정되지 않았습니다." }, { status: 500 });
  }

  let image: string;
  try {
    const body = await req.json();
    image = body.image;
    if (!image) throw new Error("이미지 없음");
  } catch {
    return NextResponse.json({ error: "올바른 이미지 데이터가 없습니다." }, { status: 400 });
  }

  const prompt = `이 냉장고 사진에서 보이는 모든 식재료를 찾아서 JSON 형식으로만 응답해주세요.
반드시 재료 이름은 한국어로 작성하세요.
형식: {"ingredients": ["재료1", "재료2", ...]}
설명 없이 JSON만 출력하세요.`;

  try {
    const response = await fetch(`${BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${OPENROUTER_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          {
            role: "user",
            content: [
              { type: "image_url", image_url: { url: image } },
              { type: "text", text: prompt },
            ],
          },
        ],
        max_tokens: 2000,
      }),
      signal: AbortSignal.timeout(60000),
    });

    if (response.status === 429) {
      return NextResponse.json(
        { error: "요청이 너무 많습니다. 잠시 후 다시 시도해주세요." },
        { status: 429 }
      );
    }

    if (!response.ok) {
      const err = await response.text();
      console.error("OpenRouter error:", err);
      return NextResponse.json({ error: "AI 분석 중 오류가 발생했습니다." }, { status: 500 });
    }

    const data = await response.json();
    const content: string = data.choices?.[0]?.message?.content ?? "";

    // [C-4] JSON 블록 추출 — 탐욕적 패턴 대신 비탐욕적으로 개선
    // /\{[\s\S]*\}/ 는 역추적이 크게 발생할 수 있으므로 \{[^{}]*\} 를 기반으로 중첩 1단계까지 허용
    const jsonMatch = content.match(/\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}/);
    if (!jsonMatch) {
      return NextResponse.json({ error: "재료를 인식하지 못했습니다. 다시 시도해주세요." }, { status: 422 });
    }

    const parsed = JSON.parse(jsonMatch[0]);

    // [C-4] Array.isArray + string 요소 검증 + 최대 50개 제한
    const rawIngredients: unknown = parsed.ingredients;
    if (!Array.isArray(rawIngredients)) {
      return NextResponse.json({ error: "재료 목록 형식이 올바르지 않습니다." }, { status: 422 });
    }
    const ingredients: string[] = rawIngredients
      .filter((x): x is string => typeof x === "string" && x.trim().length > 0)
      .slice(0, 50);

    return NextResponse.json({ ingredients });
  } catch (err) {
    console.error("analyze-image error:", err);
    return NextResponse.json({ error: "이미지를 인식할 수 없습니다." }, { status: 500 });
  }
}
