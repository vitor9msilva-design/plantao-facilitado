// Plantão Facilitado — função "plantao-ia" (Supabase Edge Function)
// Otimizada para baixa latência, suporte a thinkingConfig e fallback automático de modelos.

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (obj: unknown, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { ...CORS, "Content-Type": "application/json" } });

type Msg = { role: string; content: string };
type Resp = { text?: string; erro?: string; status?: number; uso?: unknown; corpo?: ReadableStream<Uint8Array> | null };

// ---------- Google Gemini ----------
const espera = (ms: number) => new Promise((r) => setTimeout(r, ms));
const SOBRECARGA = new Set([429, 500, 502, 503, 504]);

async function geminiUmaVez(
  model: string,
  messages: Msg[],
  key: string,
  tier = "default",
  stream = false,
  pedido = "",
  semRaciocinio = false
) {
  const generationConfig: Record<string, unknown> = { maxOutputTokens: 16384 };

  // Mantém o pensamento (thinkingLevel): "low" para velocidade no prontuário/receitas,
  // e padrão/alto no modo "complex" (revisor).
  const valido = ["minimal", "low", "medium", "high"].includes(pedido) ? pedido : "";
  const nivel = valido || Deno.env.get("RACIOCINIO") || (tier === "complex" ? "" : "low");

  if (nivel && !semRaciocinio) {
    generationConfig.thinkingConfig = { thinkingLevel: nivel };
  }

  const metodo = stream ? "streamGenerateContent?alt=sse" : "generateContent";
  const baseUrl = Deno.env.get("GEMINI_URL_BASE") || "https://generativelanguage.googleapis.com";

  const r = await fetch(`${baseUrl}/v1beta/models/${model}:${metodo}`, {
    method: "POST",
    headers: { "x-goog-api-key": key, "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: messages.map((m) => ({
        role: m.role === "assistant" ? "model" : "user",
        parts: [{ text: String(m.content) }],
      })),
      generationConfig,
    }),
  });

  if (stream && r.ok) return { r, data: {} as any };
  const data = await r.json().catch(() => ({}));
  return { r, data };
}

async function gemini(messages: Msg[], tier: string, stream = false, pedido = ""): Promise<Resp> {
  const key = Deno.env.get("GEMINI_API_KEY");
  if (!key) return { erro: "Falta o secret GEMINI_API_KEY no Supabase", status: 500 };

  // Slugs originais do seu projeto + fallbacks universais da API do Google caso algum dê 404
  const listaModelos = tier === "complex"
    ? [
        Deno.env.get("MODELO_COMPLEXO") || "gemini-3.1-pro-preview",
        "gemini-2.5-pro",
        "gemini-1.5-pro"
      ]
    : [
        Deno.env.get("MODELO") || "gemini-3.8-flash",
        Deno.env.get("MODELO_RESERVA") || "gemini-3.7-flash",
        "gemini-2.5-flash",
        "gemini-2.0-flash"
      ];

  // Remove duplicados mantendo a ordem de prioridade
  const tentativas = [...new Set(listaModelos.filter(Boolean))];

  let r: Response | null = null, data: any = {}, model = tentativas[0], semRaciocinio = false;

  for (let i = 0; i < tentativas.length; i++) {
    model = tentativas[i];
    semRaciocinio = false;

    ({ r, data } = await geminiUmaVez(model, messages, key, tier, stream, pedido, semRaciocinio));

    // Se o modelo não aceitar thinkingConfig (status 400), repete na hora sem raciocínio
    if (!r.ok && r.status === 400 && /think/i.test(data?.error?.message || "")) {
      semRaciocinio = true;
      ({ r, data } = await geminiUmaVez(model, messages, key, tier, stream, pedido, true));
    }

    if (r.ok) break;

    // Se o nome do modelo não existir na API (404), pula imediatamente para o próximo da lista
    if (r.status === 404) continue;

    // Se for sobrecarga momentânea (503/429), espera 600ms e tenta mais uma vez antes de trocar de modelo
    const st = data?.error?.status || "";
    const sobrecarga = SOBRECARGA.has(r.status) || st === "UNAVAILABLE" || /high demand|overloaded/i.test(data?.error?.message || "");
    const cotaEsgotada = /quota|billing/i.test(data?.error?.message || "") && r.status === 429;
    
    if (sobrecarga && !cotaEsgotada) {
      await espera(600);
      ({ r, data } = await geminiUmaVez(model, messages, key, tier, stream, pedido, semRaciocinio));
      if (r.ok) break;
      continue; // Continua para o modelo de reserva
    }

    break;
  }

  if (!r || !r.ok) {
    const status = r?.status || 502;
    const msg = data?.error?.message || `erro ${status}`;
    const st = data?.error?.status || "";
    const amigavel = /high demand|overloaded|UNAVAILABLE/i.test(msg + st) || status === 503
        ? "O Gemini está sobrecarregado agora. Tente de novo em alguns segundos."
      : status === 429 || st === "RESOURCE_EXHAUSTED" ? "Limite de uso do Gemini atingido, tente em 1 minuto"
      : /API key not valid|API_KEY_INVALID/i.test(msg) ? "Chave do Gemini inválida"
      : /billing|FAILED_PRECONDITION/i.test(msg + st) ? "Faturamento do Google não ativado para esta chave"
      : status === 404 ? `Nenhum modelo compatível encontrado (último testado: "${model}")`
      : msg;
    return { erro: amigavel, status: status === 429 ? 429 : 502 };
  }

  // Repassa o fluxo SSE bruto quando o site pedir streaming
  if (stream && r.body) {
    return { corpo: r.body };
  }

  const cand = data.candidates?.[0];
  const text = (cand?.content?.parts || [])
    .filter((p: { thought?: boolean; text?: string }) => !p.thought && p.text)
    .map((p: { text: string }) => p.text)
    .join("");

  if (!text) {
    const motivo = cand?.finishReason || data.promptFeedback?.blockReason || "sem resposta";
    return { erro: motivo === "MAX_TOKENS" ? "A resposta ficou longa demais, tente de novo" : `O Gemini não respondeu (${motivo})`, status: 502 };
  }
  return { text, uso: { ...data.usageMetadata, modelo: model } };
}

// ---------- Anthropic Claude (alternativa) ----------
async function claude(messages: Msg[], tier: string, stream = false): Promise<Resp> {
  const key = Deno.env.get("ANTHROPIC_API_KEY");
  if (!key) return { erro: "Falta o secret ANTHROPIC_API_KEY no Supabase", status: 500 };
  const model = tier === "complex"
    ? (Deno.env.get("MODELO_COMPLEXO") || "claude-opus-5-5")
    : (Deno.env.get("MODELO") || "claude-sonnet-5-5");
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json" },
    body: JSON.stringify({ model, max_tokens: 4096, messages, stream }),
  });
  if (stream && r.ok && r.body) return { corpo: r.body };
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const msg = data?.error?.message || `erro ${r.status}`;
    const amigavel = r.status === 429 ? "Limite de uso atingido, tente em 1 minuto"
      : /credit|billing/i.test(msg) ? "Créditos da API acabaram — recarregue no Console da Anthropic"
      : r.status === 401 ? "Chave da Anthropic inválida" : msg;
    return { erro: amigavel, status: r.status === 429 ? 429 : 502 };
  }
  const text = (data.content || []).filter((b: { type: string }) => b.type === "text").map((b: { text: string }) => b.text).join("");
  return { text, uso: data.usage };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  if (req.method !== "POST") return json({ erro: "Método não permitido" }, 405);

  const COFRE = Deno.env.get("COFRE");
  if (!COFRE) return json({ erro: "Falta o secret COFRE no Supabase" }, 500);

  let body: { cofre?: string; messages?: unknown; tier?: string; stream?: boolean; nivel?: string };
  try { body = await req.json(); } catch { return json({ erro: "Pedido inválido" }, 400); }

  if (body.cofre !== COFRE) return json({ erro: "Chave do site não autorizada para a IA" }, 403);

  const messages = Array.isArray(body.messages) ? (body.messages as Msg[]) : null;
  if (!messages || !messages.length || JSON.stringify(messages).length > 300_000)
    return json({ erro: "Conteúdo vazio ou grande demais" }, 400);

  const provedor = (Deno.env.get("PROVEDOR") || "gemini").toLowerCase();
  try {
    const stream = body.stream === true;
    const out = provedor === "claude"
      ? await claude(messages, body.tier || "default", stream)
      : await gemini(messages, body.tier || "default", stream, String(body.nivel || ""));

    if (out.erro) return json({ erro: out.erro }, out.status || 502);
    if (out.corpo) {
      return new Response(out.corpo, {
        headers: {
          ...CORS,
          "Content-Type": "text/event-stream; charset=utf-8",
          "Cache-Control": "no-cache, no-transform",
          "X-Accel-Buffering": "no",
        },
      });
    }
    return json({ text: out.text, uso: out.uso });
  } catch (e) {
    return json({ erro: "Falha ao falar com a IA: " + (e instanceof Error ? e.message : String(e)) }, 502);
  }
});