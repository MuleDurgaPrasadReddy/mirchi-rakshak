import { Link, useRouterState } from "@tanstack/react-router";
import { Home, BarChart3, MessageCircle, User, Scan } from "lucide-react";
import { useLang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const items = [
  { to: "/home", icon: Home, key: "dashboard" as const, fallbackLabel: "HOME" },
  { to: "/market", icon: BarChart3, key: "marketplace" as const, fallbackLabel: "MARKET PRICE" },
  { to: "/scan", icon: Scan, key: "scan" as const, primary: true, fallbackLabel: "SCAN" },
  { to: "/chat", icon: MessageCircle, key: "chat" as const, fallbackLabel: "ASSISTANT" },
  { to: "/profile", icon: User, key: "profile" as const, fallbackLabel: "PROFILE" },
];

export function BottomNav() {
  const { t } = useLang();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <>
      <div className="h-28" aria-hidden />
      <nav className="fixed bottom-3 left-1/2 -translate-x-1/2 w-[calc(100%-1.5rem)] max-w-[410px] z-40">
        <div className="bg-white/95 backdrop-blur-md rounded-[28px] shadow-[0_12px_32px_-8px_rgba(0,0,0,0.12)] border border-stone-200/70 flex items-center justify-around px-2 py-2">
          {items.map(({ to, icon: Icon, key, primary, fallbackLabel }) => {
            const active = pathname.startsWith(to);
            if (primary) {
              return (
                <Link
                  key={to}
                  to={to}
                  className="bg-[#a23d1d] hover:bg-[#8f3417] text-white -mt-7 size-14 rounded-2xl grid place-items-center shadow-lg shadow-orange-950/30 ring-4 ring-[#fafaf9] active:scale-95 transition shrink-0"
                  aria-label={t(key)}
                >
                  <Icon className="size-6 stroke-[2.2]" />
                </Link>
              );
            }

            return (
              <Link
                key={to}
                to={to}
                className={cn(
                  "flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-2xl transition-all min-w-14",
                  active
                    ? "bg-[#dcfce7] text-[#15803d] font-bold shadow-xs"
                    : "text-stone-400 hover:text-stone-600 font-medium",
                )}
                aria-label={t(key)}
              >
                <Icon className="size-5 stroke-[2.2]" />
                <span className="text-[10px] font-semibold tracking-wide leading-none mt-0.5">
                  {t(key)}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
