import { createServerFn } from "@tanstack/react-start";
import { requireSupabaseAuth, toValidUuid } from "@/integrations/supabase/auth-middleware";
import { supabase as defaultSupabase } from "@/integrations/supabase/client";

const GATEWAY = "https://ai.gateway.lovable.dev/v1/chat/completions";

function getApiKey(): string | undefined {
  const k = (
    process.env.GEMINI_API_KEY ||
    process.env.VITE_GEMINI_API_KEY ||
    process.env.LOVABLE_API_KEY ||
    process.env.VITE_LOVABLE_API_KEY
  )?.trim();

  return k && k.length > 5 ? k : undefined;
}

const scanSystem = `You are MirchiRakshak AI, an expert plant pathologist specializing in chili (Capsicum annuum) crop, leaf, stem, and pod scan diagnosis.

CRITICAL SCAN IDENTIFICATION INSTRUCTIONS:
1. SUBJECT IDENTIFICATION & VERIFICATION:
   - Examine the image carefully before diagnosing. Identify the primary subject in the photo.
   - IF THE PHOTO IS A HUMAN / PERSON / FACE / BODY / SELFIE:
     Set "is_chili_leaf": false,
     Set "disease": "The uploaded image is a human photo and does not match a chili leaf"
       (In Telugu: "అప్‌లోడ్ చేసిన ఫోటో మనిషిది - మిరప ఆకుతో పోలలేదు", In Hindi: "अपलोड की गई फोटो एक व्यक्ति की है और मिर्च के पत्ते से मेल नहीं खाती"),
     Set "invalid_reason": "This photo contains a person and does not match a chili leaf image. Please capture a clear photo of a chili plant leaf or pod.",
     Set "confidence": 0, "severity": "None", "treatment": [].
   - IF THE PHOTO IS ANOTHER PLANT LEAF OR NON-CHILI ITEM (e.g. Mango leaf, Tomato leaf, Cotton leaf, Rose leaf, Neem leaf, Animal, Furniture, Object):
     Identify the actual plant or object (e.g., "Mango leaf", "Tomato leaf", "Cotton leaf", "Object").
     Set "is_chili_leaf": false,
     Set "disease": "The uploaded image appears to be a [Detected Plant/Object] and does not match a chili leaf"
       (e.g., "The uploaded image is a Mango leaf and does not match a chili leaf" or in Telugu/Hindi equivalent),
     Set "invalid_reason": "This image appears to be a [Detected Plant/Object] and does not match a chili crop leaf. Please scan a chili leaf or plant.",
     Set "confidence": 0, "severity": "None", "treatment": [].

2. IF IT IS A VALID CHILI CROP / LEAF / POD:
   - Set "is_chili_leaf": true.
   - Perform an advanced multi-modal vision diagnosis.
   - Accurately diagnose ANY disease, pest infestation, nutrient deficiency, fungal pathogen, viral infection, or physiological condition affecting the chili crop.
   - Provide concrete, field-tested remedies in "treatment" (include organic formulas like Neem oil, fermented sour buttermilk, Jeevamrut, Trichoderma AND ICAR recommended chemical fungicide/insecticide dosages).

3. Output Format: Respond ONLY with valid JSON matching this structure:
{
  "is_chili_leaf": boolean,
  "invalid_reason": string,
  "disease": string,
  "is_healthy": boolean,
  "confidence": number,
  "severity": "None" | "Low" | "Moderate" | "High" | "Critical",
  "affected_area": string,
  "risk_level": "Low" | "Medium" | "High",
  "recommendation": string,
  "treatment": [{ "step": string, "detail": string }],
  "recovery_days": number
}
Output ONLY valid JSON — no markdown code fences, no extra text.`;

import {
  analyzeImageOffline,
  getOfflineChatReply,
  isPredictionSupportedByImage,
  ScanResult,
} from "./diseaseDataset";

function normalizeScanResult(parsed: ScanResult, language?: string): ScanResult {
  const diseaseText = (parsed.disease || "").toLowerCase();
  const invalidReason = (parsed.invalid_reason || "").toLowerCase();

  const isPerson =
    diseaseText.includes("person") ||
    diseaseText.includes("human") ||
    diseaseText.includes("face") ||
    diseaseText.includes("selfie") ||
    diseaseText.includes("మన్షి") ||
    diseaseText.includes("వ్యక్తి") ||
    invalidReason.includes("person") ||
    invalidReason.includes("human");

  const isMango =
    diseaseText.includes("mango") ||
    diseaseText.includes("మామిడి") ||
    diseaseText.includes("आम") ||
    invalidReason.includes("mango") ||
    invalidReason.includes("మామిడి") ||
    invalidReason.includes("आम");

  const isOtherNonChili =
    isMango ||
    diseaseText.includes("tomato") ||
    diseaseText.includes("cotton") ||
    diseaseText.includes("neem") ||
    diseaseText.includes("rose") ||
    diseaseText.includes("papaya") ||
    diseaseText.includes("banana") ||
    diseaseText.includes("guava") ||
    diseaseText.includes("other plant") ||
    diseaseText.includes("non-chili") ||
    invalidReason.includes("other plant") ||
    invalidReason.includes("non-chili");

  const isUnmatched =
    isPerson ||
    isOtherNonChili ||
    diseaseText.includes("not match") ||
    diseaseText.includes("does not match") ||
    diseaseText.includes("పోలలేదు") ||
    diseaseText.includes("नहीं खाती") ||
    parsed.is_chili_leaf === false ||
    String(parsed.is_chili_leaf).toLowerCase() === "false";

  if (isUnmatched) {
    const isTe = language === "te";
    const isHi = language === "hi";

    let title = parsed.disease;
    let reason = parsed.invalid_reason;

    if (isMango) {
      title = isTe
        ? "అప్‌లోడ్ చేసిన ఫోటో మామిడి ఆకు - మిరప ఆకుతో పోలలేదు"
        : isHi
          ? "अपलोड की गई फोटो आम के पत्ते की है और मिर्च के पत्ते से मेल नहीं खाती"
          : "The uploaded image is a Mango leaf and does not match a chili leaf";
      reason = isTe
        ? "ఈ ఫోటో మామిడి ఆకు (Mango leaf). ఇది మిరప ఆకుతో పోలడం లేదు. దయచేసి మిరప ఆకును మాత్రమే స్కాన్ చేయండి."
        : isHi
          ? "यह फोटो आम के पत्ते की है। यह मिर्च के पत्ते से मेल नहीं खाती। कृपया मिर्च के पौधे की फोटो लें।"
          : "The scanned image is a Mango leaf and does not match a chili crop leaf profile. Please scan or upload a clear photo of a chili plant leaf or pod.";
    } else if (isPerson) {
      title = isTe
        ? "అప్‌లోడ్ చేసిన ఫోటో మనిషిది - మిరప ఆకుతో పోలలేదు"
        : isHi
          ? "अपलोड की गई फोटो एक व्यक्ति की है और मिर्च के पत्ते से मेल नहीं खाती"
          : "The uploaded image is a human photo and does not match a chili leaf";
      reason = isTe
        ? "ఈ ఫోటోలో మనిషి ఉన్నారు. ఇది మిరప ఆకు లేదా మొక్క ఫొటోతో పోలడం లేదు. దయచేసి మిరప ఆకును మాత్రమే స్కాన్ చేయండి."
        : isHi
          ? "इस फोटो में व्यक्ति दिखाई दे रहा है। यह मिर्च के पत्ते की फोटो से मेल नहीं खाती। कृपया मिर्च के पत्ते की फोटो लें।"
          : "This image contains a person and does not match a chili leaf image. Please capture a clear photo of a chili leaf or plant.";
    }

    return {
      ...parsed,
      is_chili_leaf: false,
      disease: title || "The uploaded image is not a chili leaf",
      invalid_reason: reason || "The scanned image does not match a chili leaf.",
      confidence: 0,
      severity: "None",
      treatment: [],
    };
  }

  return {
    ...parsed,
    is_chili_leaf: true,
  };
}

async function callGeminiVision({
  apiKey,
  systemPrompt,
  userPrompt,
  imageBase64OrUrl,
  language,
}: {
  apiKey: string;
  systemPrompt: string;
  userPrompt: string;
  imageBase64OrUrl: string;
  language?: string;
}): Promise<ScanResult> {
  const isDirectGeminiKey = apiKey.startsWith("AIza");

  if (isDirectGeminiKey) {
    const models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"];

    let mimeType = "image/jpeg";
    let pureBase64 = imageBase64OrUrl;
    if (imageBase64OrUrl.startsWith("data:")) {
      const parts = imageBase64OrUrl.split(",");
      const match = parts[0].match(/data:(.*?);base64/);
      if (match) mimeType = match[1];
      pureBase64 = parts[1];
    }

    const body = {
      contents: [
        {
          role: "user",
          parts: [
            { text: `${systemPrompt}\n\nTask: ${userPrompt}` },
            {
              inline_data: {
                mime_type: mimeType,
                data: pureBase64,
              },
            },
          ],
        },
      ],
      generationConfig: {
        response_mime_type: "application/json",
        temperature: 0.2,
      },
    };

    let lastError: Error | null = null;
    for (const modelName of models) {
      const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`;
      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (res.ok) {
          const json = await res.json();
          let jsonText = json.candidates?.[0]?.content?.parts?.[0]?.text ?? "{}";
          jsonText = jsonText.replace(/```json/g, "").replace(/```/g, "").trim();
          const parsed = JSON.parse(jsonText) as ScanResult;
          return normalizeScanResult(parsed, language);
        } else {
          const errText = await res.text();
          lastError = new Error(`Gemini API (${modelName}) HTTP ${res.status}: ${errText}`);
        }
      } catch (e) {
        lastError = e instanceof Error ? e : new Error(String(e));
      }
    }

    throw lastError || new Error("All Gemini vision endpoints failed");
  } else {
    const imageUrl = imageBase64OrUrl.startsWith("data:")
      ? imageBase64OrUrl
      : `data:image/jpeg;base64,${imageBase64OrUrl}`;

    const res = await fetch(GATEWAY, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({
        model: "google/gemini-2.5-flash",
        messages: [
          { role: "system", content: systemPrompt },
          {
            role: "user",
            content: [
              { type: "text", text: userPrompt },
              { type: "image_url", image_url: { url: imageUrl } },
            ],
          },
        ],
        response_format: { type: "json_object" },
      }),
    });

    if (!res.ok) {
      throw new Error(`AI Gateway status ${res.status}`);
    }

    const json = await res.json();
    const contentText = json.choices?.[0]?.message?.content ?? "{}";
    const parsed = JSON.parse(contentText) as ScanResult;
    return normalizeScanResult(parsed, language);
  }
}

export const analyzeScan = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((data: unknown) => {
    const d = data as {
      imageBase64?: string;
      imageUrl?: string;
      language?: string;
      imageStats?: {
        greenRatio?: number;
        foliageRatio?: number;
        skinRatio?: number;
        brownSpotRatio?: number;
        yellowRatio?: number;
        darkGreenRatio?: number;
        glossyRatio?: number;
      };
      predictedClass?: string;
    };
    if (!d?.imageBase64 && !d?.imageUrl) throw new Error("image required");
    return {
      imageBase64: d.imageBase64,
      imageUrl: d.imageUrl,
      imageStats: d.imageStats,
      predictedClass: d.predictedClass,
      language: d.language ?? "en",
    };
  })
  .handler(async ({ data }): Promise<ScanResult> => {
    const key = getApiKey();
    const imgPayload = data.imageBase64 || data.imageUrl || "";

    const greenRatio = data.imageStats?.greenRatio ?? 0;
    const foliageRatio = data.imageStats?.foliageRatio ?? 0;
    const skinRatio = data.imageStats?.skinRatio ?? 0;
    const darkGreenRatio = data.imageStats?.darkGreenRatio ?? 0;
    const glossyRatio = data.imageStats?.glossyRatio ?? 0;
    const plantRatio = greenRatio + foliageRatio;
    const hasLesionOrYellowing = (data.imageStats?.brownSpotRatio ?? 0) > 0.02 || (data.imageStats?.yellowRatio ?? 0) > 0.04;

    // Check if client image stats indicate a person photo or Mango leaf photo
    const isPersonStats = skinRatio >= 0.12 || (skinRatio >= 0.04 && (skinRatio > plantRatio * 0.4 || plantRatio < 0.12));
    const isMangoStats = darkGreenRatio >= 0.35 && glossyRatio >= 0.02;

    // Suppress misleading local predicted class if person photo, Mango leaf, or if local model claims healthy despite lesions/yellowing
    let effectivePredictedClass = (isPersonStats || isMangoStats) ? undefined : data.predictedClass;
    if (
      effectivePredictedClass &&
      !isPredictionSupportedByImage(effectivePredictedClass, data.imageStats)
    ) {
      effectivePredictedClass = undefined;
    }
    if (effectivePredictedClass === "Chilli___healthy" && hasLesionOrYellowing) {
      effectivePredictedClass = undefined;
    }

    // 1. Dataset offline fallback if API key is missing
    if (!key) {
      console.info("[MirchiRakshak] Gemini API Key missing. Using built-in offline disease dataset.");
      return analyzeImageOffline(imgPayload, data.language, data.imageStats, effectivePredictedClass);
    }

    // 2. Try online Gemini API vision diagnosis with offline dataset fallback on failure
    try {
      const langName = data.language === "te" ? "Telugu (తెలుగు)" : data.language === "hi" ? "Hindi (हिंदी)" : "English";

      const promptText = isMangoStats
        ? `CRITICAL VERIFICATION: This photo appears to be a Mango leaf (or non-chili tree leaf). Inspect the leaf species carefully. If it is a Mango leaf or another plant species (not chili), set "is_chili_leaf": false and set "disease": "The uploaded image is a Mango leaf and does not match a chili leaf". Respond in ${langName}.`
        : isPersonStats
          ? `CRITICAL VERIFICATION: This photo appears to be a selfie or face photo of a person. Check if the image contains a human face, person, or body. If it is a person, set "is_chili_leaf": false and "disease": "The uploaded image is a human photo and does not match a chili leaf". Respond in ${langName}.`
          : effectivePredictedClass
            ? `Diagnose this chili crop photo online. Respond in ${langName}. Context from local classifier: '${effectivePredictedClass}'. Perform a full vision diagnosis.`
            : `Diagnose this uploaded photo online. Respond in ${langName}. First verify if photo contains a human, a Mango leaf, or another plant species (e.g. Tomato, Cotton, Rose, Neem) before diagnosing.`;

      return await callGeminiVision({
        apiKey: key,
        systemPrompt: scanSystem,
        userPrompt: promptText,
        imageBase64OrUrl: imgPayload,
        language: data.language,
      });
    } catch (e) {
      console.warn("[MirchiRakshak] Online Gemini diagnosis unavailable. Using local disease dataset fallback:", e);
      return analyzeImageOffline(imgPayload, data.language, data.imageStats, effectivePredictedClass);
    }
  });

const chatSystem = `You are MirchiRakshak, an expert chili farming advisor for Indian farmers.
Be concise, warm, and practical. Prefer low-cost, locally-available solutions.
Reply in the same language the farmer used (English, Hindi, or Telugu). Keep replies under 120 words unless asked otherwise.
Use bullet lists sparingly for step-by-step guidance.`;

async function callGeminiChat({
  apiKey,
  systemPrompt,
  messages,
}: {
  apiKey: string;
  systemPrompt: string;
  messages: { role: string; content: string }[];
}): Promise<string> {
  const isDirectGeminiKey = apiKey.startsWith("AIza");

  if (isDirectGeminiKey) {
    const models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"];
    const contents = messages.map((m) => ({
      role: m.role === "assistant" ? "model" : "user",
      parts: [{ text: m.content }],
    }));

    const body = {
      system_instruction: {
        parts: [{ text: systemPrompt }],
      },
      contents,
    };

    let lastError: Error | null = null;
    for (const modelName of models) {
      const endpoint = `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`;
      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });

        if (res.ok) {
          const json = await res.json();
          return json.candidates?.[0]?.content?.parts?.[0]?.text ?? "";
        } else {
          const errText = await res.text();
          lastError = new Error(`Gemini Chat API (${modelName}) HTTP ${res.status}: ${errText}`);
        }
      } catch (e) {
        lastError = e instanceof Error ? e : new Error(String(e));
      }
    }

    throw lastError || new Error("Gemini Chat API failed");
  } else {
    const res = await fetch(GATEWAY, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({
        model: "google/gemini-2.5-flash",
        messages: [{ role: "system", content: systemPrompt }, ...messages],
      }),
    });
    if (!res.ok) throw new Error(`Gateway HTTP ${res.status}`);
    const json = await res.json();
    return json.choices?.[0]?.message?.content ?? "";
  }
}

export const chatAssistant = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((data: unknown) => {
    const d = data as { messages?: { role: "user" | "assistant"; content: string }[]; language?: string };
    if (!Array.isArray(d?.messages)) throw new Error("messages required");
    return { messages: d.messages, language: d.language ?? "en" };
  })
  .handler(async ({ data }): Promise<{ reply: string }> => {
    const key = getApiKey();

    // 1. Dataset offline fallback if API key missing
    if (!key) {
      return { reply: getOfflineChatReply(data.messages, data.language) };
    }

    try {
      const langName = data.language === "te" ? "Telugu" : data.language === "hi" ? "Hindi" : "English";

      const reply = await callGeminiChat({
        apiKey: key,
        systemPrompt: `${chatSystem}\nPreferred language: ${langName}.`,
        messages: data.messages,
      });

      return { reply };
    } catch (e) {
      console.warn("[MirchiRakshak] Online chat assistant fallback to local dataset engine:", e);
      return { reply: getOfflineChatReply(data.messages, data.language) };
    }
  });

export type WeatherData = {
  current: { temp: number; humidity: number; wind: number; code: number; time: string };
  daily: { date: string; tmax: number; tmin: number; rain: number; code: number }[];
  risk: "Low" | "Medium" | "High";
  advice: string;
  sprayWindow: string;
};

export const fetchWeather = createServerFn({ method: "GET" })
  .inputValidator((data: unknown) => {
    const d = data as { lat?: number; lon?: number };
    return { lat: d?.lat ?? 16.3067, lon: d?.lon ?? 80.4365 }; // Guntur default
  })
  .handler(async ({ data }): Promise<WeatherData> => {
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${data.lat}&longitude=${data.lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto&forecast_days=7`;

    const buildResult = (
      humidity: number,
      temp: number,
      wind: number,
      currentCode: number,
      currentTime: string,
      daily: { date: string; tmax: number; tmin: number; rain: number; code: number }[],
    ): WeatherData => {
      let risk: "Low" | "Medium" | "High" = "Low";
      if (humidity > 75 && temp > 26) risk = "High";
      else if (humidity > 60) risk = "Medium";

      const advice = risk === "High"
        ? "High humidity favours thrips and leaf curl. Inspect the underside of leaves today."
        : risk === "Medium"
          ? "Moderate risk. Continue routine monitoring."
          : "Conditions are favourable. Good time for foliar spray if planned.";

      const sprayWindow = wind < 10 ? "Tomorrow 06:00 – 08:00" : "Delay spray — wind too high";

      return {
        current: { temp, humidity, wind, code: currentCode, time: currentTime },
        daily,
        risk,
        advice,
        sprayWindow,
      };
    };

    const fallback = (): WeatherData => {
      const today = new Date();
      const daily = Array.from({ length: 7 }, (_, i) => {
        const d = new Date(today);
        d.setDate(today.getDate() + i);
        return {
          date: d.toISOString().slice(0, 10),
          tmax: 32 - (i % 3),
          tmin: 24 - (i % 2),
          rain: i === 2 ? 4 : 0,
          code: 2,
        };
      });
      return buildResult(68, 29, 6, 2, today.toISOString(), daily);
    };

    try {
      const res = await fetch(url);
      if (!res.ok) return fallback();
      const j = await res.json();
      const humidity = Math.round(j.current.relative_humidity_2m);
      const temp = Math.round(j.current.temperature_2m);
      const wind = Math.round(j.current.wind_speed_10m);
      const daily = j.daily.time.map((t: string, i: number) => ({
        date: t,
        tmax: Math.round(j.daily.temperature_2m_max[i]),
        tmin: Math.round(j.daily.temperature_2m_min[i]),
        rain: j.daily.precipitation_sum[i] ?? 0,
        code: j.daily.weather_code[i],
      }));
      return buildResult(humidity, temp, wind, j.current.weather_code, j.current.time, daily);
    } catch {
      return fallback();
    }
  });

export const saveScan = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((d: unknown) => d as ScanResult & { image_url?: string; language?: string })
  .handler(async ({ data, context }) => {
    const rawUserId = context?.userId || "anonymous";
    const userId = toValidUuid(rawUserId);
    const scanData = {
      user_id: userId,
      image_url: data.image_url ?? null,
      disease: data.disease,
      confidence: data.confidence,
      severity: data.severity,
      affected_area: data.affected_area,
      risk_level: data.risk_level,
      recommendation: data.recommendation,
      treatment: data.treatment as unknown as never,
      recovery_days: data.recovery_days,
      is_healthy: data.is_healthy,
      is_chili_leaf: data.is_chili_leaf,
      invalid_reason: data.invalid_reason ?? null,
      language: data.language ?? "en",
    };

    // 1. First attempt using context.supabase (if user is authenticated via Supabase session)
    if (context?.supabase) {
      try {
        let result = await context.supabase.from("scans").insert(scanData).select("id").single();
        if (result.error && /invalid_reason|is_chili_leaf|schema cache/i.test(result.error.message)) {
          const { is_chili_leaf: _isChiliLeaf, invalid_reason: _invalidReason, ...legacyScanData } = scanData;
          result = await context.supabase.from("scans").insert(legacyScanData).select("id").single();
        }
        if (!result.error && result.data?.id) return { id: result.data.id };
      } catch (e) {
        console.warn("[saveScan] User client insert attempt:", e);
      }
    }

    // 2. Try server-side admin client (bypasses RLS for Firebase / non-Supabase auth users)
    try {
      const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
      let result = await supabaseAdmin.from("scans").insert(scanData).select("id").single();
      if (result.error && /invalid_reason|is_chili_leaf|schema cache/i.test(result.error.message)) {
        const { is_chili_leaf: _isChiliLeaf, invalid_reason: _invalidReason, ...legacyScanData } = scanData;
        result = await supabaseAdmin.from("scans").insert(legacyScanData).select("id").single();
      }
      if (!result.error && result.data?.id) return { id: result.data.id };
      if (result.error) console.warn("[saveScan] Admin insert warning:", result.error.message);
    } catch (adminErr) {
      console.warn("[saveScan] Admin client fallback unavailable:", adminErr);
    }

    // 3. Fallback attempt with standard default client
    try {
      let result = await defaultSupabase.from("scans").insert(scanData).select("id").single();
      if (result.error && /invalid_reason|is_chili_leaf|schema cache/i.test(result.error.message)) {
        const { is_chili_leaf: _isChiliLeaf, invalid_reason: _invalidReason, ...legacyScanData } = scanData;
        result = await defaultSupabase.from("scans").insert(legacyScanData).select("id").single();
      }
      if (!result.error && result.data?.id) return { id: result.data.id };
    } catch (defErr) {
      console.warn("[saveScan] Default client insert fallback:", defErr);
    }

    return { id: "scan-" + Date.now() };
  });

export const listScans = createServerFn({ method: "GET" })
  .handler(async ({ context }: any) => {
    try {
      if (context?.supabase) {
        const { data, error } = await context.supabase
          .from("scans")
          .select("*")
          .order("created_at", { ascending: false })
          .limit(50);
        if (!error && data) return data;
      }
      try {
        const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
        const { data, error } = await supabaseAdmin
          .from("scans")
          .select("*")
          .order("created_at", { ascending: false })
          .limit(50);
        if (!error && data) return data;
      } catch { }

      const { data, error } = await defaultSupabase
        .from("scans")
        .select("*")
        .order("created_at", { ascending: false })
        .limit(50);
      if (!error && data) return data;
    } catch (e) {
      console.warn("listScans fallback:", e);
    }
    return [];
  });
