import React, { useState, useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import {
  Bell,
  Check,
  CheckCheck,
  ChevronRight,
  Clock,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { toast } from "sonner";
import {
  loadReminders,
  completeReminder,
  getDaysRemaining,
  getReminderStatus,
  ReminderItem,
} from "@/lib/reminders";
import { useLang } from "@/lib/i18n";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

/**
 * CropScanIcon: Reticle camera scan brackets with center leaf.
 */
function CropScanIcon({ className = "size-5 text-[#15803d]" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M4 8V5a1 1 0 0 1 1-1h3" />
      <path d="M16 4h3a1 1 0 0 1 1 1v3" />
      <path d="M20 16v3a1 1 0 0 1-1 1h-3" />
      <path d="M8 20H5a1 1 0 0 1-1-1v-3" />
      <path
        d="M9 15C9.6 11.8 12.8 9.2 15.8 8.8C15.6 12 12.4 14.6 9 15Z"
        fill="currentColor"
      />
    </svg>
  );
}

/**
 * SprayingIcon: Trigger spray bottle with droplet spray mist.
 */
function SprayingIcon({ className = "size-5 text-[#d97706]" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M7 11h10v9a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2v-9Z" fill="currentColor" fillOpacity="0.25" />
      <path d="M10 7h4v4h-4z" />
      <path d="M14 7l4-2v4l-4-1" />
      <path d="M9 9a2.5 2.5 0 0 0 0 4" />
      <circle cx="20.5" cy="5.5" r="0.75" fill="currentColor" />
      <circle cx="22" cy="3.5" r="0.75" fill="currentColor" />
      <circle cx="21" cy="7" r="0.75" fill="currentColor" />
    </svg>
  );
}

/**
 * FertilizerIcon: Sprout with 2 leaves growing from soil line.
 */
function FertilizerIcon({ className = "size-5 text-[#7c3aed]" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M6 19h12" />
      <path
        d="M12 14.5C11.5 10.5 8 8 5.2 8.5C5.4 12 8.6 14.8 12 14.5Z"
        fill="currentColor"
      />
      <path
        d="M12 14.5C12.5 10.5 16 8 18.8 8.5C18.6 12 15.4 14.8 12 14.5Z"
        fill="currentColor"
      />
      <path d="M12 13.5v5.5" />
    </svg>
  );
}

export function NotificationCenterModal() {
  const navigate = useNavigate();
  const { t } = useLang();
  const [isOpen, setIsOpen] = useState(false);
  const [reminders, setReminders] = useState<ReminderItem[]>([]);

  useEffect(() => {
    const sync = () => {
      setReminders(loadReminders());
    };
    sync();
    window.addEventListener("mirchi_reminders_updated", sync);
    return () => window.removeEventListener("mirchi_reminders_updated", sync);
  }, []);

  // Filter ONLY tasks that are due and need to be reminded and marked as done!
  const tasksDue = reminders.filter((i) => i.enabled && getDaysRemaining(i.dueDate) <= 0);
  const dueCount = tasksDue.length;

  // Upcoming future tasks (for info when all are done)
  const upcomingTasks = reminders
    .filter((i) => i.enabled && getDaysRemaining(i.dueDate) > 0)
    .sort((a, b) => getDaysRemaining(a.dueDate) - getDaysRemaining(b.dueDate));

  const handleMarkComplete = (id: ReminderItem["id"], title: string) => {
    const updated = completeReminder(id);
    setReminders(updated);
    toast.success(`${title} marked done! Next reminder scheduled.`);
  };

  const handleMarkAllDone = () => {
    tasksDue.forEach((t) => completeReminder(t.id));
    setReminders(loadReminders());
    toast.success("All due tasks marked as completed!");
  };

  return (
    <>
      {/* Bell Button in App Header */}
      <button
        onClick={() => setIsOpen(true)}
        className="size-10 rounded-full bg-white border border-stone-200/80 grid place-items-center shadow-xs relative hover:bg-stone-50 active:scale-95 transition cursor-pointer"
        aria-label="Open notifications"
        title="Farm notifications & reminders"
      >
        <Bell className="size-[18px] text-stone-700" />
        {dueCount > 0 ? (
          <span className="absolute -top-1 -right-1 size-5 bg-red-500 text-white text-[10px] font-black rounded-full grid place-items-center ring-2 ring-white animate-pulse">
            {dueCount}
          </span>
        ) : (
          <span className="absolute top-2.5 right-2.5 size-2 bg-emerald-500 rounded-full ring-2 ring-white" />
        )}
      </button>

      {/* Notifications Dialog */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-md w-[92vw] sm:w-full rounded-[28px] p-5 sm:p-6 bg-white border border-stone-200 shadow-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader className="text-left space-y-1 pb-2 border-b border-stone-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="size-8 rounded-xl bg-[#e8f8ee] border border-[#cdebd6] grid place-items-center text-emerald-700 shrink-0">
                  <Bell className="size-4" />
                </div>
                <div>
                  <DialogTitle className="text-lg font-black text-stone-900 tracking-tight">
                    {t("dueReminders")}
                  </DialogTitle>
                  <DialogDescription className="text-xs text-stone-500">
                    {t("tasksNeedAttention")}
                  </DialogDescription>
                </div>
              </div>

              {dueCount > 1 && (
                <button
                  onClick={handleMarkAllDone}
                  className="text-[11px] font-bold text-emerald-700 hover:text-emerald-800 flex items-center gap-1 bg-emerald-50 border border-emerald-200/80 px-2.5 py-1 rounded-full active:scale-95 transition"
                >
                  <CheckCheck className="size-3.5" />
                  <span>{t("markAllDone")}</span>
                </button>
              )}
            </div>
          </DialogHeader>

          {/* If there are tasks due: Show ONLY those tasks */}
          {dueCount > 0 ? (
            <div className="space-y-3 my-2">
              <div className="p-3 rounded-2xl bg-rose-50/80 border border-rose-200/80 flex items-start gap-2.5">
                <AlertTriangle className="size-4 text-rose-600 shrink-0 mt-0.5" />
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-bold text-rose-950">
                    {dueCount} {dueCount === 1 ? "task needs" : "tasks need"} your attention today
                  </p>
                  <p className="text-[11px] text-rose-800/80 mt-0.5 leading-snug">
                    Complete and mark done to reset the reminder cycle.
                  </p>
                </div>
              </div>

              {tasksDue.map((item) => {
                const daysLeft = getDaysRemaining(item.dueDate);
                const status = getReminderStatus(daysLeft);

                return (
                  <div
                    key={item.id}
                    className="p-3.5 rounded-2xl border border-rose-200 bg-[#fffbfa] shadow-2xs transition"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2.5 min-w-0">
                        <div
                          className={`size-10 rounded-xl grid place-items-center shrink-0 ${
                            item.id === "scan"
                              ? "bg-[#dcfce7]"
                              : item.id === "spraying"
                                ? "bg-[#fef3c7]"
                                : "bg-[#ede9fe]"
                          }`}
                        >
                          {item.id === "scan" && <CropScanIcon className="size-5 text-[#15803d]" />}
                          {item.id === "spraying" && <SprayingIcon className="size-5 text-[#d97706]" />}
                          {item.id === "fertilizer" && <FertilizerIcon className="size-5 text-[#7c3aed]" />}
                        </div>

                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <p className="text-[13px] font-bold text-stone-900 leading-tight">
                              {item.title}
                            </p>
                            <span className="text-[10px] text-stone-400 font-semibold">
                              (every {item.intervalDays}d)
                            </span>
                          </div>
                          <p className="text-[11px] text-stone-600 mt-0.5 leading-snug">
                            {item.subtitle}
                          </p>
                        </div>
                      </div>

                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10.5px] font-black shrink-0 ${status.pillClass}`}
                      >
                        {status.text}
                      </span>
                    </div>

                    {/* Action buttons for this specific due task */}
                    <div className="flex items-center justify-between gap-2 mt-3 pt-2.5 border-t border-rose-100/80">
                      {item.id === "scan" ? (
                        <button
                          onClick={() => {
                            setIsOpen(false);
                            navigate({ to: "/scan" });
                          }}
                          className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-extrabold transition active:scale-95 shadow-2xs"
                        >
                          Scan Crop Now →
                        </button>
                      ) : (
                        <div />
                      )}

                      <button
                        onClick={() => handleMarkComplete(item.id, item.title)}
                        className="px-3 py-1.5 rounded-xl bg-white border border-stone-300 text-stone-800 text-xs font-bold hover:bg-stone-50 transition active:scale-95 flex items-center gap-1.5 shadow-2xs"
                      >
                        <Check className="size-3.5 stroke-[3] text-emerald-600" />
                        <span>{t("markDone")}</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            /* Empty State: All tasks are completed! */
            <div className="py-6 px-4 text-center space-y-3">
              <div className="size-14 rounded-full bg-emerald-50 border border-emerald-200 grid place-items-center text-emerald-600 mx-auto shadow-2xs">
                <CheckCircle2 className="size-8" />
              </div>

              <div>
                <h4 className="text-base font-black text-stone-900">
                  {t("allUpToDate")}
                </h4>
                <p className="text-xs text-stone-500 max-w-xs mx-auto mt-1 leading-relaxed">
                  {t("noDueTasks")}
                </p>
              </div>

              {/* Upcoming preview */}
              {upcomingTasks.length > 0 && (
                <div className="p-3 rounded-2xl bg-[#f4fbf7] border border-[#d8f3e2] text-left space-y-1.5 mt-3">
                  <p className="text-[10.5px] font-extrabold uppercase tracking-wider text-emerald-800">
                    Next Upcoming Reminders
                  </p>
                  {upcomingTasks.slice(0, 2).map((t) => (
                    <div key={t.id} className="flex items-center justify-between text-xs py-0.5">
                      <span className="font-semibold text-stone-700">{t.title}</span>
                      <span className="font-bold text-emerald-700">
                        In {getDaysRemaining(t.dueDate)} days
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Dialog Footer */}
          <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs">
            <span className="text-[11px] text-stone-400 flex items-center gap-1">
              <Clock className="size-3 text-stone-400" />
              {dueCount > 0 ? `${dueCount} pending task` : "All up to date"}
            </span>

            <button
              onClick={() => setIsOpen(false)}
              className="text-stone-700 font-bold hover:text-stone-900 px-3 py-1.5 rounded-lg border border-stone-200 active:scale-95 transition"
            >
              Close
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
