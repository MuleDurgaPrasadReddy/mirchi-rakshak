import { useEffect } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { queryOptions, useSuspenseQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ScanLine } from "lucide-react";
import { PhoneShell } from "@/components/PhoneShell";
import { BottomNav } from "@/components/BottomNav";
import { listScans } from "@/lib/ai.functions";
import { useLang } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { loadLocalScans, type ScanRecord } from "@/lib/scans";

const scansQO = queryOptions({
  queryKey: ["scans"],
  queryFn: async (): Promise<ScanRecord[]> => {
    try {
      const res = await listScans();
      const serverScans = Array.isArray(res) ? (res as ScanRecord[]) : [];
      if (typeof window !== "undefined") {
        const localScans = loadLocalScans();
        const map = new Map<string, ScanRecord>();
        for (const s of localScans) map.set(s.id, s);
        for (const s of serverScans) map.set(s.id, s);
        return Array.from(map.values()).sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      }
      return serverScans;
    } catch (e) {
      console.warn("Scans query fallback:", e);
      if (typeof window !== "undefined") return loadLocalScans();
      return [];
    }
  },
  staleTime: 60 * 1000,
});

export const Route = createFileRoute("/_authenticated/history")({
  head: () => ({ meta: [{ title: "Scan history — MirchiRakshak AI" }] }),
  loader: async ({ context }) => { await context.queryClient.ensureQueryData(scansQO); },
  component: HistoryPage,
});

function HistoryPage() {
  const { t } = useLang();
  const qc = useQueryClient();
  const scans = useSuspenseQuery(scansQO).data;

  useEffect(() => {
    const handleScansUpdate = () => {
      qc.invalidateQueries({ queryKey: ["scans"] });
    };
    window.addEventListener("mirchi_scans_updated", handleScansUpdate);
    return () => window.removeEventListener("mirchi_scans_updated", handleScansUpdate);
  }, [qc]);
  const isUnmatched = (scan: (typeof scans)[number]) =>
    scan.is_chili_leaf === false || scan.disease?.toLowerCase().includes("not matched");

  return (
    <PhoneShell>
      <header className="px-5 pt-10 pb-4 flex items-center justify-between">
        <Link to="/home" className="size-10 rounded-full bg-white ring-1 ring-black/5 grid place-items-center shadow-sm" aria-label="Back">
          <ArrowLeft className="size-4" />
        </Link>
        <h1 className="text-base font-semibold text-stone-800">{t("history")}</h1>
        <Link to="/scan" className="size-10 rounded-full bg-chili-600 text-white grid place-items-center shadow-sm shadow-chili-600/30" aria-label="New scan">
          <ScanLine className="size-4" />
        </Link>
      </header>

      <main className="px-5 space-y-3 pb-6">
        {scans.length === 0 ? (
          <div className="bg-white rounded-3xl p-8 text-center ring-1 ring-black/5 mt-8">
            <div className="text-4xl mb-3">🌶️</div>
            <p className="font-semibold text-stone-800">{t("noScans")}</p>
            <p className="text-sm text-stone-500 mt-1">{t("startFirst")}</p>
            <Link to="/scan" className="mt-6 inline-flex items-center gap-2 bg-chili-600 text-white rounded-2xl px-5 py-3 font-semibold shadow-lg shadow-chili-600/30">
              <ScanLine className="size-4" /> {t("scanCrop")}
            </Link>
          </div>
        ) : (
          scans.map((s: any) => (
            <div key={s.id} className="bg-white rounded-2xl p-4 ring-1 ring-black/5 shadow-sm flex gap-4 animate-fade">
              <div className="size-16 rounded-xl overflow-hidden bg-earth-100 shrink-0 grid place-items-center">
                {s.image_url ? (
                  <img src={s.image_url} alt="" className="w-full h-full object-cover" width={64} height={64} loading="lazy" />
                ) : (
                  <span className="text-xl">🌶️</span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2 mb-1">
                  <h3 className={cn("font-semibold truncate", isUnmatched(s) ? "text-red-900" : "text-stone-900")}>
                    {isUnmatched(s) ? t("leafNotMatched") : s.disease}
                  </h3>
                  <span className="text-[10px] text-stone-400 shrink-0">{new Date(s.created_at).toLocaleDateString()}</span>
                </div>
                <p className={cn("text-xs font-semibold", isUnmatched(s) ? "text-red-700" : s.is_healthy ? "text-leaf-600" : "text-chili-600")}>
                  {isUnmatched(s) ? t("scanAgain") : `${s.is_healthy ? t("healthy") : t("actionRequired")} · ${s.severity}`}
                </p>
                {(s.invalid_reason || s.recommendation) && (
                  <p className="text-xs text-stone-500 mt-1 line-clamp-2">{isUnmatched(s) ? s.invalid_reason || s.recommendation : s.recommendation}</p>
                )}
              </div>
            </div>
          ))
        )}
      </main>

      <BottomNav />
    </PhoneShell>
  );
}
