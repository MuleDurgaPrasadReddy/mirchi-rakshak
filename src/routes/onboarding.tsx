import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { ScanLine, CloudRain, Mic, ArrowRight, ChevronRight } from "lucide-react";
import { PhoneShell } from "@/components/PhoneShell";
import { useLang, languageOptions, type Lang } from "@/lib/i18n";
import chiliHero from "@/assets/chili-hero.jpg";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/onboarding")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "Welcome to MirchiRakshak AI" },
      { name: "description", content: "Get started with the AI assistant built for chili farmers." },
    ],
  }),
  component: Onboarding,
});

function Onboarding() {
  const { t, lang, setLang } = useLang();
  const nav = useNavigate();
  const [step, setStep] = useState(0);

  const slides = [
    { title: t("ob1t"), desc: t("ob1d"), icon: ScanLine },
    { title: t("ob2t"), desc: t("ob2d"), icon: CloudRain },
    { title: t("ob3t"), desc: t("ob3d"), icon: Mic },
  ];

  const finish = () => {
    if (typeof window !== "undefined") window.localStorage.setItem("mr-onboarded", "1");
    nav({ to: "/auth" });
  };

  if (step === 0) {
    return (
      <PhoneShell>
        <div className="relative min-h-screen flex flex-col">
          <img
            src={chiliHero}
            alt=""
            className="absolute inset-0 w-full h-[60%] object-cover"
            width={1024}
            height={1280}
          />
          <div className="absolute inset-0 h-[65%] bg-gradient-to-b from-transparent via-earth-50/20 to-earth-50" />
          <div className="relative flex-1 flex flex-col justify-end px-6 pb-8 pt-40">
            <div className="mb-auto pt-4">
              <div className="inline-flex items-center gap-2 bg-white/80 backdrop-blur-md rounded-full px-3 py-1.5 ring-1 ring-black/5 shadow-sm">
                <span className="size-2 rounded-full bg-chili-600 animate-pulse" />
                <span className="text-[11px] font-bold uppercase tracking-widest text-stone-700">MirchiRakshak AI</span>
              </div>
            </div>
            <div className="animate-rise">
              <p className="text-chili-600 font-telugu font-medium text-sm mb-1">{t("greeting")} 🙏</p>
              <h1 className="text-3xl font-bold tracking-tight leading-[1.1] text-stone-900">
                {t("growMoreChili")}
              </h1>
              <p className="mt-4 text-stone-600 text-base leading-relaxed max-w-[32ch]">
                {t("onboardingCompanion")}
              </p>

              <div className="mt-8 space-y-2">
                <p className="text-[10px] font-bold text-stone-400 uppercase tracking-widest mb-2">{t("chooseLanguage")}</p>
                <div className="grid grid-cols-3 gap-2">
                  {languageOptions.map((o) => (
                    <button
                      key={o.code}
                      onClick={() => setLang(o.code as Lang)}
                      className={cn(
                        "rounded-2xl py-3 px-2 text-sm font-semibold ring-1 transition",
                        lang === o.code
                          ? "bg-stone-900 text-white ring-stone-900"
                          : "bg-white text-stone-800 ring-black/5",
                      )}
                    >
                      {o.native}
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={() => setStep(1)}
                className="mt-8 w-full bg-chili-600 text-white rounded-2xl py-4 flex items-center justify-center gap-2 font-semibold shadow-lg shadow-chili-600/30 active:scale-[0.98] transition"
              >
                {t("getStarted")}
                <ArrowRight className="size-5" />
              </button>
            </div>
          </div>
        </div>
      </PhoneShell>
    );
  }

  const s = slides[step - 1];
  const Icon = s.icon;

  return (
    <PhoneShell>
      <div className="min-h-screen flex flex-col px-6 pt-16 pb-8">
        <div className="flex justify-between items-center mb-8">
          <div className="flex gap-1.5">
            {[1, 2, 3].map((n) => (
              <span
                key={n}
                className={cn(
                  "h-1.5 rounded-full transition-all",
                  step === n ? "w-8 bg-chili-600" : "w-1.5 bg-stone-200",
                )}
              />
            ))}
          </div>
          <button onClick={finish} className="text-sm font-semibold text-stone-500">{t("skip")}</button>
        </div>

        <div className="flex-1 flex flex-col justify-center animate-rise" key={step}>
          <div className="size-20 rounded-3xl bg-chili-100 grid place-items-center mb-8">
            <Icon className="size-10 text-chili-600" strokeWidth={2} />
          </div>
          <h2 className="text-3xl font-bold tracking-tight leading-tight text-stone-900">{s.title}</h2>
          <p className="mt-4 text-stone-600 text-base leading-relaxed">{s.desc}</p>
        </div>

        <button
          onClick={() => (step < 3 ? setStep(step + 1) : finish())}
          className="w-full bg-stone-900 text-white rounded-2xl py-4 flex items-center justify-center gap-2 font-semibold active:scale-[0.98] transition"
        >
          {step < 3 ? t("next") : t("getStarted")}
          <ChevronRight className="size-5" />
        </button>
      </div>
    </PhoneShell>
  );
}
