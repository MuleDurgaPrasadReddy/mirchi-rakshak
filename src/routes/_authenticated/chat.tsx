import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { ArrowLeft, Mic, MicOff, Send, Volume2 } from "lucide-react";
import { PhoneShell } from "@/components/PhoneShell";
import { BottomNav } from "@/components/BottomNav";
import { useLang } from "@/lib/i18n";
import { chatAssistant } from "@/lib/ai.functions";
import { useServerFn } from "@tanstack/react-start";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_authenticated/chat")({
  head: () => ({ meta: [{ title: "AI Assistant — MirchiRakshak AI" }] }),
  component: ChatPage,
});

type Msg = { role: "user" | "assistant"; content: string };

// Web Speech types (progressive enhancement)
interface SR extends EventTarget {
  lang: string; interimResults: boolean; continuous: boolean;
  start(): void; stop(): void;
  onresult: (e: { results: { [k: number]: { [k: number]: { transcript: string } } } & { length: number } }) => void;
  onend: () => void; onerror: (e: unknown) => void;
}
const getSR = (): (new () => SR) | null => {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: new () => SR; webkitSpeechRecognition?: new () => SR };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
};

function ChatPage() {
  const { t, lang } = useLang();
  const chat = useServerFn(chatAssistant);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const recRef = useRef<SR | null>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);
  useEffect(() => { inputRef.current?.focus(); }, [loading]);

  async function send(text: string) {
    const clean = text.trim();
    if (!clean || loading) return;
    const next = [...messages, { role: "user" as const, content: clean }];
    setMessages(next);
    setInput("");
    setLoading(true);
    try {
      const { reply } = await chat({ data: { messages: next, language: lang } });
      setMessages((m) => [...m, { role: "assistant", content: reply }]);
      speak(reply);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Assistant unavailable");
    } finally {
      setLoading(false);
    }
  }

  function speak(text: string) {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    try {
      const u = new SpeechSynthesisUtterance(text.slice(0, 500));
      u.lang = lang === "te" ? "te-IN" : lang === "hi" ? "hi-IN" : "en-IN";
      u.rate = 0.95;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    } catch { /* ignore */ }
  }

  function toggleMic() {
    const SR = getSR();
    if (!SR) { toast.error("Voice not supported on this device"); return; }
    if (listening) { recRef.current?.stop(); return; }
    const rec = new SR();
    rec.lang = lang === "te" ? "te-IN" : lang === "hi" ? "hi-IN" : "en-IN";
    rec.interimResults = false;
    rec.continuous = false;
    rec.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setInput(transcript);
      send(transcript);
    };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec;
    rec.start();
    setListening(true);
  }

  const suggestions = [t("suggestedQ1"), t("suggestedQ2"), t("suggestedQ3")];

  return (
    <PhoneShell>
      <header className="sticky top-0 z-30 bg-earth-50/85 backdrop-blur-lg px-5 pt-10 pb-4 flex items-center justify-between border-b border-black/5">
        <Link to="/home" className="size-10 rounded-full bg-white ring-1 ring-black/5 grid place-items-center shadow-sm" aria-label="Back">
          <ArrowLeft className="size-4" />
        </Link>
        <div className="text-center">
          <h1 className="text-base font-semibold text-stone-800">{t("chat")}</h1>
          <p className="text-[10px] font-bold text-leaf-700 uppercase tracking-widest">MirchiRakshak AI</p>
        </div>
        <div className="size-10" />
      </header>

      <main className="px-4 pb-32 pt-4 space-y-3 min-h-[70vh]">
        {messages.length === 0 && (
          <div className="text-center py-8 animate-rise">
            <div className="size-16 mx-auto mb-4 rounded-3xl bg-gradient-to-br from-chili-600 to-chili-700 grid place-items-center text-white shadow-lg shadow-chili-600/30">
              <span className="text-2xl">🌶️</span>
            </div>
            <h2 className="text-lg font-semibold text-stone-800">{t("askMeAnything")}</h2>
            <p className="text-sm text-stone-500 mt-1 max-w-[28ch] mx-auto">
              {t("chatSub")}
            </p>
            <div className="mt-6 space-y-2">
              {suggestions.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="w-full bg-white ring-1 ring-black/5 rounded-2xl py-3 px-4 text-sm text-left text-stone-700 hover:ring-chili-200 transition"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={cn("flex animate-fade", m.role === "user" ? "justify-end" : "justify-start")}>
            <div
              className={cn(
                "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap",
                m.role === "user"
                  ? "bg-chili-600 text-white rounded-br-md"
                  : "bg-white ring-1 ring-black/5 text-stone-800 rounded-bl-md shadow-sm",
              )}
            >
              {m.content}
              {m.role === "assistant" && (
                <button
                  onClick={() => speak(m.content)}
                  className="mt-2 inline-flex items-center gap-1 text-[10px] font-bold text-stone-400 uppercase tracking-wider"
                >
                  <Volume2 className="size-3" /> {t("speak")}
                </button>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white ring-1 ring-black/5 rounded-2xl px-4 py-3 flex gap-1 shadow-sm">
              <span className="size-2 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="size-2 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="size-2 bg-stone-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </main>

      <div className="fixed bottom-20 left-1/2 -translate-x-1/2 w-[calc(100%-1.5rem)] max-w-[406px] z-30">
        <form
          onSubmit={(e) => { e.preventDefault(); send(input); }}
          className="glass rounded-2xl shadow-xl ring-1 ring-black/5 flex items-center gap-2 px-3 py-2"
        >
          <button
            type="button" onClick={toggleMic}
            className={cn(
              "size-10 rounded-xl grid place-items-center shrink-0 transition",
              listening ? "bg-destructive text-white animate-pulse" : "bg-stone-100 text-stone-700",
            )}
            aria-label="Voice input"
          >
            {listening ? <MicOff className="size-4" /> : <Mic className="size-4" />}
          </button>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t("askQuestion")}
            className="flex-1 bg-transparent outline-none text-sm text-stone-800 placeholder:text-stone-400"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="size-10 rounded-xl bg-chili-600 text-white grid place-items-center shrink-0 disabled:opacity-40 shadow-md shadow-chili-600/30"
            aria-label="Send"
          >
            <Send className="size-4" />
          </button>
        </form>
      </div>

      <BottomNav />
    </PhoneShell>
  );
}
