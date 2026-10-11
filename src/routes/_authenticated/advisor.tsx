import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, PhoneCall, ShieldCheck, TrendingUp } from "lucide-react";
import { PhoneShell } from "@/components/PhoneShell";
import { BottomNav } from "@/components/BottomNav";
import { useLang } from "@/lib/i18n";
import expertFarmer from "@/assets/expert_farmer_clean.png";

export const Route = createFileRoute("/_authenticated/advisor")({
  head: () => ({ meta: [{ title: "Expert Consultation — MirchiRakshak AI" }] }),
  component: AdvisorPage,
});

export function AdvisorPage() {
  const { t, lang } = useLang();

  const handleCall = () => {
    window.location.href = "tel:8520971554";
  };

  return (
    <PhoneShell>
      <div className="min-h-screen flex flex-col pb-24 bg-stone-50">
        <header className="px-5 pt-8 pb-4 flex items-center justify-between bg-white border-b border-stone-200 sticky top-0 z-20">
          <Link
            to="/home"
            className="size-10 rounded-full bg-stone-100 grid place-items-center hover:bg-stone-200 transition"
            aria-label="Back"
          >
            <ArrowLeft className="size-4 text-stone-700" />
          </Link>
          <div className="text-center flex-1">
            <h1 className="text-base font-bold text-stone-900">{t("expertConsultation")}</h1>
          </div>
          <div className="size-10" />
        </header>

        <main className="px-5 pt-4 space-y-4 flex-1">
          {/* Forest Green Hero Banner matching home screen */}
          <section className="relative overflow-hidden bg-[#0a522a] text-white rounded-[26px] p-5 shadow-[0_12px_28px_-8px_rgba(9,82,42,0.45)]">
            <div className="flex items-center justify-between gap-2">
              <div className="flex-1 min-w-0 pr-2">
                <p className="text-[10px] uppercase tracking-[0.16em] text-emerald-100/90 font-bold flex items-center gap-1.5">
                  <TrendingUp className="size-3.5 text-white stroke-[2.5]" />
                  {t("expertConsultation")}
                </p>
                <h2 className="mt-1 text-2xl font-bold tracking-tight text-white leading-tight">
                  {t("getExpertAdvice")}
                </h2>
                <p className="text-[12px] text-emerald-100/85 mt-1 font-normal leading-relaxed">
                  {t("getExpertAdviceSub")}
                </p>
              </div>

              <div className="shrink-0 -my-4 -mr-2">
                <img
                  src={expertFarmer}
                  alt="Expert Advisor"
                  className="h-28 w-auto object-contain object-bottom select-none pointer-events-none"
                />
              </div>
            </div>
          </section>

          {/* Helpline Card */}
          <section className="rounded-3xl bg-white border border-stone-200/80 p-5 shadow-xs">
            <div className="text-center space-y-3">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 text-xs font-bold border border-emerald-200/60">
                <ShieldCheck className="size-3.5 text-emerald-600" />
                {t("helplineTitle")}
              </div>
              <p className="text-3xl font-extrabold text-stone-900 tracking-wide">8520971554</p>
              <p className="text-xs text-stone-500 font-medium">
                {t("monSatHours")}
              </p>
              <button
                onClick={handleCall}
                className="w-full rounded-2xl bg-emerald-700 hover:bg-emerald-800 active:scale-[0.98] text-white font-bold text-base shadow-lg shadow-emerald-800/25 transition flex items-center justify-center gap-2 py-3.5"
              >
                <PhoneCall className="size-5" />
                {t("callHelpline")}
              </button>
            </div>
          </section>
        </main>

        <BottomNav />
      </div>
    </PhoneShell>
  );
}
