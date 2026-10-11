import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/** Constrains content to a mobile-first canvas even on larger screens. */
export function PhoneShell({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className="min-h-screen bg-earth-100 flex justify-center">
      <div
        className={cn(
          "w-full max-w-[430px] min-h-screen bg-earth-50 relative overflow-x-hidden shadow-[0_0_60px_-20px_rgba(0,0,0,0.15)]",
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}
