import { createFileRoute, Link } from "@tanstack/react-router";
import { queryOptions, useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { ArrowLeft, Cloud, CloudRain, Droplets, Sun, Wind, MapPin } from "lucide-react";
import { PhoneShell } from "@/components/PhoneShell";
import { BottomNav } from "@/components/BottomNav";
import { fetchWeather } from "@/lib/ai.functions";
import { useUserLocation } from "@/lib/location";
import { useLang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const weatherQO = queryOptions({
  queryKey: ["weather"],
  queryFn: () => fetchWeather({ data: {} }),
  staleTime: 10 * 60 * 1000,
});

export const Route = createFileRoute("/_authenticated/weather")({
  head: () => ({ meta: [{ title: "Weather — MirchiRakshak AI" }] }),
  loader: async ({ context }) => { await context.queryClient.ensureQueryData(weatherQO); },
  component: WeatherPage,
});

const dayNames: Record<string, string[]> = {
  en: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
  te: ["ఆది", "సోమ", "మంగళ", "బుధ", "గురు", "శుక్ర", "శని"],
  hi: ["रवि", "सोम", "मंगल", "बुध", "गुरु", "शुक्र", "शनि"],
};

function WeatherPage() {
  const { t, lang } = useLang();
  const { location: userLoc } = useUserLocation();
  const initialW = useSuspenseQuery(weatherQO).data;
  const { data: w = initialW } = useQuery({
    queryKey: ["weather", userLoc?.lat, userLoc?.lon],
    queryFn: () => fetchWeather({ data: { lat: userLoc?.lat, lon: userLoc?.lon } }),
    staleTime: 10 * 60 * 1000,
    initialData: initialW,
    enabled: Boolean(userLoc?.lat && userLoc?.lon),
  });

  const localizedDays = dayNames[lang] || dayNames.en;

  return (
    <PhoneShell>
      <header className="px-5 pt-10 pb-4 flex items-center justify-between">
        <Link to="/home" className="size-10 rounded-full bg-white ring-1 ring-black/5 grid place-items-center shadow-sm" aria-label="Back">
          <ArrowLeft className="size-4" />
        </Link>
        <div className="text-center">
          <h1 className="text-base font-semibold text-stone-800 leading-tight">{t("weather")}</h1>
          <p className="text-[11px] font-medium text-emerald-800 flex items-center justify-center gap-1 mt-0.5">
            <MapPin className="size-3 text-emerald-600" /> {userLoc.district}, {userLoc.state}
          </p>
        </div>
        <div className="size-10" />
      </header>

      <main className="px-5 space-y-4">
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-sky-900 to-sky-800 text-white p-6 shadow-lg animate-rise">
          <div className="absolute -right-6 -top-6 size-32 bg-white/10 rounded-full blur-3xl" />
          <div className="absolute -left-4 bottom-0 size-24 bg-chili-500/20 rounded-full blur-2xl" />
          <div className="relative">
            <p className="text-[10px] uppercase tracking-widest text-sky-200/70 font-bold mb-1">{t("todayForecast")}</p>
            <div className="flex items-end justify-between">
              <p className="text-6xl font-medium leading-none">{w.current.temp}°</p>
              <Sun className="size-14 text-amber-300" />
            </div>
            <div className="mt-6 grid grid-cols-3 gap-2 text-xs">
              <Metric icon={<Droplets className="size-3" />} label={t("humidity")} value={`${w.current.humidity}%`} />
              <Metric icon={<Wind className="size-3" />} label={t("wind")} value={`${w.current.wind} km/h`} />
              <Metric icon={<CloudRain className="size-3" />} label={t("rainfall")} value={`${w.daily[0]?.rain ?? 0}mm`} />
            </div>
          </div>
        </section>

        {/* Spray advisory */}
        <section className={cn(
          "rounded-3xl p-5 ring-1 shadow-sm animate-rise",
          w.risk === "High" ? "bg-orange-50 ring-orange-200" :
            w.risk === "Medium" ? "bg-amber-50 ring-amber-200" :
              "bg-leaf-50 ring-leaf-200",
        )}>
          <div className="flex items-center justify-between mb-2">
            <p className="text-[10px] font-bold uppercase tracking-widest text-stone-600">{t("sprayAdvice")}</p>
            <span className={cn(
              "text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded",
              w.risk === "High" ? "bg-orange-600 text-white" :
                w.risk === "Medium" ? "bg-amber-600 text-white" :
                  "bg-leaf-600 text-white",
            )}>
              {t("diseaseRisk")}: {t(w.risk.toLowerCase() as "high" | "medium" | "low")}
            </span>
          </div>
          <p className="text-sm text-stone-800 leading-relaxed font-medium">{w.advice}</p>
          <div className="mt-3 pt-3 border-t border-black/5 flex items-center justify-between">
            <span className="text-[11px] font-bold text-stone-500 uppercase tracking-widest">{t("sprayWindow")}</span>
            <span className="text-sm font-semibold text-stone-800">{w.sprayWindow}</span>
          </div>
        </section>

        {/* 7-day forecast */}
        <section className="bg-white rounded-3xl p-5 ring-1 ring-black/5 shadow-sm animate-rise">
          <h2 className="text-sm font-semibold text-stone-800 mb-4">{t("sevenDay")}</h2>
          <div className="space-y-2">
            {w.daily.map((d, i) => (
              <div key={d.date} className="flex items-center gap-3 py-1">
                <span className="w-10 text-xs font-bold text-stone-500">
                  {i === 0 ? t("now") : localizedDays[new Date(d.date).getDay()]}
                </span>
                <Cloud className="size-4 text-stone-400" />
                <span className="w-10 text-xs text-sky-700 font-medium">{d.rain > 0 ? `${d.rain}mm` : ""}</span>
                <div className="flex-1 h-1.5 rounded-full bg-earth-100 relative overflow-hidden">
                  <div className="absolute inset-y-0 rounded-full bg-gradient-to-r from-sky-400 via-amber-400 to-chili-500"
                    style={{ left: `${((d.tmin - 15) / 25) * 100}%`, right: `${100 - ((d.tmax - 15) / 25) * 100}%` }} />
                </div>
                <span className="w-8 text-xs font-semibold text-stone-800 text-right">{d.tmax}°</span>
                <span className="w-8 text-xs text-stone-400 text-right">{d.tmin}°</span>
              </div>
            ))}
          </div>
        </section>
      </main>

      <BottomNav />
    </PhoneShell>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="bg-white/10 backdrop-blur rounded-xl p-2.5 ring-1 ring-white/10">
      <div className="flex items-center gap-1 text-sky-200/80 text-[9px] font-bold uppercase tracking-wider">
        {icon} {label}
      </div>
      <p className="text-sm font-semibold mt-0.5">{value}</p>
    </div>
  );
}
