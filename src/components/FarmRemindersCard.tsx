import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { ChevronRight, Settings2, Bell, BellRing, Check, Clock, RefreshCw, X } from "lucide-react";
import { toast } from "sonner";
import {
  loadReminders,
  saveReminders,
  completeReminder,
  updateReminderIntervals,
  getDaysRemaining,
  getReminderStatus,
  requestNotificationPermission,
  triggerBrowserNotificationIfDue,
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
 * CalendarCheckBadge: Calendar outline with top binder rings and center checkmark.
 */
function CalendarCheckBadge({ className = "size-7 text-[#15803d]" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 28 28"
      fill="none"
      className={className}
      stroke="currentColor"
      strokeWidth="2.3"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="3.5" y="5.5" width="21" height="19" rx="4" />
      <path d="M8.5 3v4.5" />
      <path d="M19.5 3v4.5" />
      <path d="M8.5 14.5l3.5 3.5 7-7" />
    </svg>
  );
}

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

/**
 * ListRemindersIcon: Bulleted checklist icon.
 */
function ListRemindersIcon({ className = "size-4 text-[#006837]" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="9" y1="6" x2="20" y2="6" />
      <line x1="9" y1="12" x2="20" y2="12" />
      <line x1="9" y1="18" x2="20" y2="18" />
      <circle cx="4.5" cy="6" r="1.5" fill="currentColor" />
      <circle cx="4.5" cy="12" r="1.5" fill="currentColor" />
      <circle cx="4.5" cy="18" r="1.5" fill="currentColor" />
    </svg>
  );
}

export function FarmRemindersCard() {
  const navigate = useNavigate();
  const { t, lang } = useLang();
  const [reminders, setReminders] = useState<ReminderItem[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isViewAllOpen, setIsViewAllOpen] = useState(false);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>("default");

  // Localized helper
  const getLocalizedStatusText = (daysLeft: number) => {
    if (daysLeft <= 0) return t("dueToday");
    if (daysLeft === 1) return lang === "te" ? "రేపు గడువు" : lang === "hi" ? "कल देय" : "Due tomorrow";
    return lang === "te" ? `${daysLeft} రోజుల్లో` : lang === "hi" ? `${daysLeft} दिनों में` : `In ${daysLeft} days`;
  };

  const getLocalizedTaskTitle = (id: string, defaultTitle: string) => {
    if (id === "scan") return t("scanCropReminder");
    if (id === "spraying") return t("sprayingReminder");
    if (id === "fertilizer") return t("fertilizerReminder");
    return defaultTitle;
  };

  const getLocalizedEveryText = (days: number) => {
    if (lang === "te") return `(ప్రతి ${days} రోజులకు)`;
    if (lang === "hi") return `(हर ${days} दिन)`;
    return `(every ${days}d)`;
  };

  // Input states for reminder intervals (days)
  const [scanDays, setScanDays] = useState(3);
  const [sprayDays, setSprayDays] = useState(6);
  const [fertDays, setFertDays] = useState(10);

  // Load reminders & initialize
  useEffect(() => {
    const syncReminders = () => {
      const items = loadReminders();
      setReminders(items);

      const scanItem = items.find((i) => i.id === "scan");
      const sprayItem = items.find((i) => i.id === "spraying");
      const fertItem = items.find((i) => i.id === "fertilizer");

      if (scanItem) setScanDays(scanItem.intervalDays);
      if (sprayItem) setSprayDays(sprayItem.intervalDays);
      if (fertItem) setFertDays(fertItem.intervalDays);
    };

    syncReminders();
    window.addEventListener("mirchi_reminders_updated", syncReminders);

    if (typeof window !== "undefined" && "Notification" in window) {
      setNotificationPermission(Notification.permission);
    }

    return () => {
      window.removeEventListener("mirchi_reminders_updated", syncReminders);
    };
  }, []);

  // Check and trigger reminder notifications once on load
  useEffect(() => {
    if (reminders.length === 0) return;

    // Trigger browser alert if granted
    triggerBrowserNotificationIfDue(reminders);

    // In-app alert for due tasks
    const dueTasks = reminders.filter((i) => i.enabled && getDaysRemaining(i.dueDate) <= 0);
    if (dueTasks.length > 0) {
      const toastKey = "mirchi_toast_notified_" + new Date().toDateString();
      if (!sessionStorage.getItem(toastKey)) {
        sessionStorage.setItem(toastKey, "true");
        toast.warning(`🌱 Farm Reminder: ${dueTasks[0].title} is due today!`, {
          description: dueTasks[0].subtitle,
          action: {
            label: dueTasks[0].id === "scan" ? "Scan Leaf" : "View Advisory",
            onClick: () => {
              if (dueTasks[0].id === "scan") {
                navigate({ to: "/scan" });
              } else {
                navigate({ to: "/chat" });
              }
            },
          },
        });
      }
    }
  }, [reminders, navigate]);

  // Derived metrics
  const scanItem = reminders.find((i) => i.id === "scan");
  const sprayItem = reminders.find((i) => i.id === "spraying");
  const fertItem = reminders.find((i) => i.id === "fertilizer");

  const scanDaysLeft = scanItem ? getDaysRemaining(scanItem.dueDate) : 0;
  const sprayDaysLeft = sprayItem ? getDaysRemaining(sprayItem.dueDate) : 3;
  const fertDaysLeft = fertItem ? getDaysRemaining(fertItem.dueDate) : 7;

  const scanStatus = getReminderStatus(scanDaysLeft);
  const sprayStatus = getReminderStatus(sprayDaysLeft);
  const fertStatus = getReminderStatus(fertDaysLeft);

  const tasksDueCount = [scanDaysLeft, sprayDaysLeft, fertDaysLeft].filter((d) => d <= 0).length;

  // Next upcoming task description
  const nextTaskSubtitle =
    scanDaysLeft <= 0
      ? "Next: Scan your crop"
      : sprayDaysLeft <= 0
        ? "Next: Crop spraying"
        : fertDaysLeft <= 0
          ? "Next: Apply fertilizer"
          : scanDaysLeft <= sprayDaysLeft && scanDaysLeft <= fertDaysLeft
            ? `Next: Scan in ${scanDaysLeft} day${scanDaysLeft === 1 ? "" : "s"}`
            : `Next: Spraying in ${sprayDaysLeft} days`;

  // Handle Mark Done (Advance cycle by interval)
  const handleMarkDone = (e: React.MouseEvent, id: ReminderItem["id"]) => {
    e.stopPropagation();
    e.preventDefault();
    const updated = completeReminder(id);
    setReminders(updated);
    const item = updated.find((i) => i.id === id);
    toast.success(`Completed! Next reminder set for ${item?.intervalDays || 3} days from now.`);
  };

  // Handle Save Reminders Dialog
  const handleSaveIntervals = () => {
    const updated = updateReminderIntervals({
      scan: scanDays,
      spraying: sprayDays,
      fertilizer: fertDays,
    });
    setReminders(updated);
    setIsSettingsOpen(false);
    toast.success("Farm reminder schedule updated successfully!");
  };

  // Enable Browser Notifications
  const handleEnableNotifications = async () => {
    const perm = await requestNotificationPermission();
    setNotificationPermission(perm);
    if (perm === "granted") {
      toast.success("Browser notifications enabled! You will be reminded when field tasks are due.");
      triggerBrowserNotificationIfDue(reminders);
    } else {
      toast.error("Notification permission not granted. You can still see in-app alerts.");
    }
  };

  return (
    <>
      <div className="bg-[#f4fbf7] border border-[#d8f3e2] rounded-[28px] p-4.5 sm:p-5 relative overflow-hidden shadow-2xs">
        {/* Decorative Botanical Leaves in bottom-right corner */}
        <svg
          className="absolute bottom-0 right-0 w-44 h-40 pointer-events-none text-[#bbf7d0] opacity-55"
          viewBox="0 0 160 140"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M160 140 C145 90 120 40 85 10 C80 50 100 110 160 140 Z"
            fill="currentColor"
          />
          <path
            d="M160 140 C140 100 115 65 92 38"
            stroke="white"
            strokeWidth="1.5"
            opacity="0.6"
          />
          <path
            d="M140 140 C125 105 95 80 60 70 C65 100 95 125 140 140 Z"
            fill="currentColor"
            opacity="0.85"
          />
          <path
            d="M140 140 C120 112 100 95 72 82"
            stroke="white"
            strokeWidth="1.2"
            opacity="0.6"
          />
        </svg>

        {/* Top Header */}
        <div className="flex items-start justify-between gap-3 relative z-10 mb-3.5">
          <div className="flex items-start gap-3 min-w-0">
            <div className="size-12 rounded-2xl bg-[#e8f8ee] border border-[#cdebd6] grid place-items-center shrink-0 shadow-2xs">
              <CalendarCheckBadge className="size-6 text-[#15803d]" />
            </div>
            <div className="min-w-0">
              <p className="text-[10.5px] font-extrabold uppercase tracking-widest text-[#006837]">
                {t("farmRemindersTitle")}
              </p>
              <h3 className="text-[21px] font-black text-[#003816] tracking-tight leading-tight mt-0.5">
                {tasksDueCount > 0 ? `${tasksDueCount} ${t("dueToday")}` : t("allUpToDate")}
              </h3>
              <p className="text-xs font-semibold text-[#525a66] mt-0.5">
                {nextTaskSubtitle}
              </p>
            </div>
          </div>

          <div className="flex flex-col items-end shrink-0">
            {/* Tasks Due Pill with animated red dot */}
            <div className="relative">
              <span className="bg-[#dcfce7] px-3 py-1 rounded-full text-xs font-black text-[#004d20] shadow-2xs inline-block">
                {tasksDueCount > 0 ? `${tasksDueCount} ${t("dueToday")}` : t("allUpToDate")}
              </span>
              {tasksDueCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 size-2.5 bg-red-500 rounded-full ring-2 ring-white animate-pulse" />
              )}
            </div>

            {/* Quick Settings Action */}
            <button
              onClick={() => setIsSettingsOpen(true)}
              className="mt-2 flex items-center gap-1 text-[11px] font-bold text-stone-600 hover:text-emerald-800 transition active:scale-95"
              title="Set reminder intervals"
              aria-label="Set reminder days"
            >
              <Settings2 className="size-3.5 text-emerald-700" />
              <ChevronRight className="size-4 text-stone-900 stroke-[2.5]" />
            </button>
          </div>
        </div>

        {/* Reminders List (3 items) */}
        <div className="space-y-2 relative z-10">
          {/* Task 1: Crop scan reminder */}
          <div className="flex items-center justify-between gap-2 p-2 rounded-2xl hover:bg-white/60 active:scale-[0.99] transition group">
            <Link to="/scan" className="flex items-center gap-2.5 min-w-0 flex-1">
              <div className="size-10 rounded-xl bg-[#dcfce7] grid place-items-center shrink-0">
                <CropScanIcon className="size-5 text-[#15803d]" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <p className="text-[13px] font-bold text-stone-900 leading-tight">
                    {t("scanCropReminder")}
                  </p>
                  <span className="text-[10px] text-stone-400 font-semibold">
                    {getLocalizedEveryText(scanDays)}
                  </span>
                </div>
                <p className="text-[11px] text-[#525a66] font-medium leading-tight mt-0.5 truncate">
                  Inspect your chilli leaves
                </p>
              </div>
            </Link>

            <div className="flex items-center gap-1.5 shrink-0">
              <span
                className={`px-3 py-1 rounded-full text-[11px] font-black shrink-0 shadow-2xs ${scanStatus.pillClass}`}
              >
                {getLocalizedStatusText(scanDaysLeft)}
              </span>
              {scanDaysLeft <= 0 && (
                <button
                  onClick={(e) => handleMarkDone(e, "scan")}
                  className="size-7 rounded-full bg-emerald-600 text-white grid place-items-center hover:bg-emerald-700 active:scale-90 transition shadow-2xs"
                  title="Mark done for today"
                  aria-label="Mark scan done"
                >
                  <Check className="size-3.5 stroke-[3]" />
                </button>
              )}
            </div>
          </div>

          {/* Task 2: Spraying reminder (No navigation) */}
          <div className="flex items-center justify-between gap-2 p-2 rounded-2xl hover:bg-white/60 transition group">
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <div className="size-10 rounded-xl bg-[#fef3c7] grid place-items-center shrink-0">
                <SprayingIcon className="size-5 text-[#d97706]" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <p className="text-[13px] font-bold text-stone-900 leading-tight">
                    {t("sprayingReminder")}
                  </p>
                  <span className="text-[10px] text-stone-400 font-semibold">
                    {getLocalizedEveryText(sprayDays)}
                  </span>
                </div>
                <p className="text-[11px] text-[#525a66] font-medium leading-tight mt-0.5 truncate">
                  Follow your crop-protection schedule
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1.5 shrink-0">
              <span
                className={`px-3 py-1 rounded-full text-[11px] font-black shrink-0 shadow-2xs ${sprayStatus.pillClass}`}
              >
                {getLocalizedStatusText(sprayDaysLeft)}
              </span>
              {sprayDaysLeft <= 0 && (
                <button
                  onClick={(e) => handleMarkDone(e, "spraying")}
                  className="size-7 rounded-full bg-amber-600 text-white grid place-items-center hover:bg-amber-700 active:scale-90 transition shadow-2xs"
                  title="Mark done for today"
                  aria-label="Mark spraying done"
                >
                  <Check className="size-3.5 stroke-[3]" />
                </button>
              )}
            </div>
          </div>

          {/* Task 3: Fertilizer reminder (No navigation) */}
          <div className="flex items-center justify-between gap-2 p-2 rounded-2xl hover:bg-white/60 transition group">
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <div className="size-10 rounded-xl bg-[#ede9fe] grid place-items-center shrink-0">
                <FertilizerIcon className="size-5 text-[#7c3aed]" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-1.5">
                  <p className="text-[13px] font-bold text-stone-900 leading-tight">
                    {t("fertilizerReminder")}
                  </p>
                  <span className="text-[10px] text-stone-400 font-semibold">
                    {getLocalizedEveryText(fertDays)}
                  </span>
                </div>
                <p className="text-[11px] text-[#525a66] font-medium leading-tight mt-0.5 truncate">
                  Apply fertilizer as per your schedule
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1.5 shrink-0">
              <span
                className={`px-3 py-1 rounded-full text-[11px] font-black shrink-0 shadow-2xs ${fertStatus.pillClass}`}
              >
                {getLocalizedStatusText(fertDaysLeft)}
              </span>
              {fertDaysLeft <= 0 && (
                <button
                  onClick={(e) => handleMarkDone(e, "fertilizer")}
                  className="size-7 rounded-full bg-purple-600 text-white grid place-items-center hover:bg-purple-700 active:scale-90 transition shadow-2xs"
                  title="Mark done for today"
                  aria-label="Mark fertilizer done"
                >
                  <Check className="size-3.5 stroke-[3]" />
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions: View All Reminders + Set Reminder Days */}
        <div className="pt-3 mt-2 border-t border-[#d8f3e2]/70 flex items-center justify-between relative z-10">
          <button
            type="button"
            onClick={() => setIsViewAllOpen(true)}
            className="flex items-center gap-2 text-xs font-black text-[#006837] hover:text-[#004d20] transition group cursor-pointer"
          >
            <ListRemindersIcon className="size-4 text-[#006837]" />
            <span>{t("viewAllReminders")}</span>
            <ChevronRight className="size-3.5 text-[#006837] stroke-[2.5] group-hover:translate-x-0.5 transition" />
          </button>

          <button
            onClick={() => setIsSettingsOpen(true)}
            className="flex items-center gap-1.5 text-xs font-bold text-emerald-800 bg-white/80 border border-emerald-200/80 px-2.5 py-1 rounded-full hover:bg-emerald-50 active:scale-95 transition shadow-2xs cursor-pointer"
          >
            <Settings2 className="size-3.5 text-emerald-700" />
            <span>{lang === "te" ? "రోజులు మార్చు" : lang === "hi" ? "दिन बदलें" : "Set Days"}</span>
          </button>
        </div>
      </div>

      {/* Set Reminders Dialog */}
      <Dialog open={isSettingsOpen} onOpenChange={setIsSettingsOpen}>
        <DialogContent className="max-w-md w-[92vw] sm:w-full rounded-[28px] p-6 bg-white border border-stone-200/90 shadow-2xl">
          <DialogHeader className="text-left space-y-1">
            <div className="flex items-center gap-2 text-emerald-700 font-extrabold text-xs uppercase tracking-wider">
              <CalendarCheckBadge className="size-4 text-emerald-700" />
              <span>Configure Schedule</span>
            </div>
            <DialogTitle className="text-xl font-black text-stone-900 tracking-tight">
              Set Farm Reminder Days
            </DialogTitle>
            <DialogDescription className="text-xs text-stone-500">
              Enter every how many days you want to be reminded for each farming task.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 my-2">
            {/* Setting 1: Crop Scan */}
            <div className="p-3.5 rounded-2xl bg-[#f4fbf7] border border-[#d8f3e2] flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-xl bg-[#dcfce7] grid place-items-center shrink-0">
                  <CropScanIcon className="size-5 text-[#15803d]" />
                </div>
                <div>
                  <p className="text-sm font-bold text-stone-900 leading-tight">Crop Scan</p>
                  <p className="text-[11px] text-stone-500 leading-tight mt-0.5">
                    Leaf health & pest inspection
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  onClick={() => setScanDays((prev) => Math.max(1, prev - 1))}
                  className="size-8 rounded-lg bg-white border border-stone-200 grid place-items-center text-stone-700 font-bold hover:bg-stone-50 active:scale-95 transition"
                >
                  -
                </button>
                <div className="flex items-center gap-0.5 bg-white border border-stone-200 px-2 py-1 rounded-lg">
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={scanDays}
                    onChange={(e) => setScanDays(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-8 text-center text-sm font-extrabold text-stone-900 focus:outline-none"
                  />
                  <span className="text-[11px] font-semibold text-stone-400">days</span>
                </div>
                <button
                  type="button"
                  onClick={() => setScanDays((prev) => prev + 1)}
                  className="size-8 rounded-lg bg-white border border-stone-200 grid place-items-center text-stone-700 font-bold hover:bg-stone-50 active:scale-95 transition"
                >
                  +
                </button>
              </div>
            </div>

            {/* Setting 2: Spraying */}
            <div className="p-3.5 rounded-2xl bg-[#fffbeb] border border-[#fde68a] flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-xl bg-[#fef3c7] grid place-items-center shrink-0">
                  <SprayingIcon className="size-5 text-[#d97706]" />
                </div>
                <div>
                  <p className="text-sm font-bold text-stone-900 leading-tight">Spraying</p>
                  <p className="text-[11px] text-stone-500 leading-tight mt-0.5">
                    Pesticide & fungicide schedule
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  onClick={() => setSprayDays((prev) => Math.max(1, prev - 1))}
                  className="size-8 rounded-lg bg-white border border-stone-200 grid place-items-center text-stone-700 font-bold hover:bg-stone-50 active:scale-95 transition"
                >
                  -
                </button>
                <div className="flex items-center gap-0.5 bg-white border border-stone-200 px-2 py-1 rounded-lg">
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={sprayDays}
                    onChange={(e) => setSprayDays(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-8 text-center text-sm font-extrabold text-stone-900 focus:outline-none"
                  />
                  <span className="text-[11px] font-semibold text-stone-400">days</span>
                </div>
                <button
                  type="button"
                  onClick={() => setSprayDays((prev) => prev + 1)}
                  className="size-8 rounded-lg bg-white border border-stone-200 grid place-items-center text-stone-700 font-bold hover:bg-stone-50 active:scale-95 transition"
                >
                  +
                </button>
              </div>
            </div>

            {/* Setting 3: Fertilizer */}
            <div className="p-3.5 rounded-2xl bg-[#f5f3ff] border border-[#ddd6fe] flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-xl bg-[#ede9fe] grid place-items-center shrink-0">
                  <FertilizerIcon className="size-5 text-[#7c3aed]" />
                </div>
                <div>
                  <p className="text-sm font-bold text-stone-900 leading-tight">Fertilizers</p>
                  <p className="text-[11px] text-stone-500 leading-tight mt-0.5">
                    NPK & foliar nutrient dosage
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  type="button"
                  onClick={() => setFertDays((prev) => Math.max(1, prev - 1))}
                  className="size-8 rounded-lg bg-white border border-stone-200 grid place-items-center text-stone-700 font-bold hover:bg-stone-50 active:scale-95 transition"
                >
                  -
                </button>
                <div className="flex items-center gap-0.5 bg-white border border-stone-200 px-2 py-1 rounded-lg">
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={fertDays}
                    onChange={(e) => setFertDays(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-8 text-center text-sm font-extrabold text-stone-900 focus:outline-none"
                  />
                  <span className="text-[11px] font-semibold text-stone-400">days</span>
                </div>
                <button
                  type="button"
                  onClick={() => setFertDays((prev) => prev + 1)}
                  className="size-8 rounded-lg bg-white border border-stone-200 grid place-items-center text-stone-700 font-bold hover:bg-stone-50 active:scale-95 transition"
                >
                  +
                </button>
              </div>
            </div>

            {/* Browser Notifications Toggle */}
            <div className="p-3 rounded-2xl bg-stone-50 border border-stone-200 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="size-9 rounded-xl bg-white border border-stone-200 grid place-items-center text-stone-700 shrink-0">
                  {notificationPermission === "granted" ? (
                    <BellRing className="size-4.5 text-emerald-600" />
                  ) : (
                    <Bell className="size-4.5 text-stone-500" />
                  )}
                </div>
                <div>
                  <p className="text-xs font-bold text-stone-900 leading-tight">
                    Device Notifications
                  </p>
                  <p className="text-[10.5px] text-stone-500 leading-tight mt-0.5">
                    {notificationPermission === "granted"
                      ? "Active • Reminds you when due"
                      : "Receive browser reminders"}
                  </p>
                </div>
              </div>

              {notificationPermission === "granted" ? (
                <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-full flex items-center gap-1">
                  <Check className="size-3 stroke-[3]" /> Active
                </span>
              ) : (
                <button
                  type="button"
                  onClick={handleEnableNotifications}
                  className="text-xs font-bold text-emerald-800 bg-emerald-100 hover:bg-emerald-200 px-3 py-1 rounded-full active:scale-95 transition"
                >
                  Enable
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2.5 pt-2">
            <button
              type="button"
              onClick={() => {
                setScanDays(3);
                setSprayDays(6);
                setFertDays(10);
              }}
              className="px-3 py-2.5 rounded-xl border border-stone-200 text-stone-600 text-xs font-bold hover:bg-stone-50 active:scale-95 transition flex items-center gap-1.5"
            >
              <RefreshCw className="size-3.5" />
              Reset (3, 6, 10d)
            </button>
            <button
              type="button"
              onClick={handleSaveIntervals}
              className="flex-1 py-2.5 rounded-xl bg-[#006837] hover:bg-[#00522c] text-white text-xs font-extrabold tracking-wide active:scale-95 transition shadow-sm"
            >
              Save Reminders
            </button>
          </div>
        </DialogContent>
      </Dialog>

      {/* View All Reminders & Set Dates Dialog */}
      <Dialog open={isViewAllOpen} onOpenChange={setIsViewAllOpen}>
        <DialogContent className="max-w-md w-[92vw] sm:w-full rounded-[28px] p-5 sm:p-6 bg-white border border-stone-200 shadow-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader className="text-left space-y-1 pb-2 border-b border-stone-100">
            <div className="flex items-center gap-2">
              <div className="size-8 rounded-xl bg-[#e8f8ee] border border-[#cdebd6] grid place-items-center text-emerald-700 shrink-0">
                <ListRemindersIcon className="size-4 text-emerald-700" />
              </div>
              <div>
                <DialogTitle className="text-lg font-black text-stone-900 tracking-tight">
                  {t("allRemindersTitle")}
                </DialogTitle>
                <DialogDescription className="text-xs text-stone-500">
                  {t("allRemindersSub")}
                </DialogDescription>
              </div>
            </div>
          </DialogHeader>

          <div className="space-y-3 my-2">
            {reminders.map((item) => {
              const daysLeft = getDaysRemaining(item.dueDate);
              const status = getReminderStatus(daysLeft);
              const isDue = daysLeft <= 0;

              const setDateFormatted = item.lastCompletedAt
                ? new Date(item.lastCompletedAt).toLocaleDateString(
                    lang === "te" ? "te-IN" : lang === "hi" ? "hi-IN" : "en-GB",
                    {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    }
                  )
                : (lang === "te" ? "సెట్ చేయలేదు" : lang === "hi" ? "सेट नहीं" : "Not set");

              const dueDateFormatted = item.dueDate
                ? new Date(item.dueDate).toLocaleDateString(
                    lang === "te" ? "te-IN" : lang === "hi" ? "hi-IN" : "en-GB",
                    {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    }
                  )
                : (lang === "te" ? "సెట్ చేయలేదు" : lang === "hi" ? "सेट नहीं" : "Not set");

              return (
                <div
                  key={item.id}
                  className="p-3.5 rounded-2xl border border-stone-200/80 bg-[#fbfcfb] shadow-2xs space-y-2.5"
                >
                  {/* Top Task Header */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5 min-w-0">
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
                            {getLocalizedTaskTitle(item.id, item.title)}
                          </p>
                          <span className="text-[10px] text-stone-500 bg-stone-100 px-2 py-0.5 rounded-full font-semibold">
                            {lang === "te" ? `ప్రతి ${item.intervalDays} రోజులకు` : lang === "hi" ? `हर ${item.intervalDays} दिन` : `Every ${item.intervalDays}d`}
                          </span>
                        </div>
                        <p className="text-[11px] text-stone-500 mt-0.5 leading-snug">
                          {item.subtitle}
                        </p>
                      </div>
                    </div>

                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10.5px] font-black shrink-0 ${status.pillClass}`}
                    >
                      {getLocalizedStatusText(daysLeft)}
                    </span>
                  </div>

                  {/* Scheduled Dates Information */}
                  <div className="grid grid-cols-2 gap-2 bg-stone-50/90 p-2.5 rounded-xl border border-stone-100 text-xs">
                    <div>
                      <p className="text-[10px] uppercase font-bold text-stone-400 tracking-wider">
                        {lang === "te" ? "సెట్ చేసిన తేదీ" : lang === "hi" ? "सेट की गई तारीख" : "Reminder Set Date"}
                      </p>
                      <p className="font-bold text-stone-700 mt-0.5">
                        {setDateFormatted}
                      </p>
                    </div>

                    <div>
                      <p className="text-[10px] uppercase font-bold text-stone-400 tracking-wider">
                        {lang === "te" ? "తదుపరి గడువు తేదీ" : lang === "hi" ? "अगली देय तारीख" : "Next Reminder Date"}
                      </p>
                      <p className={`font-black mt-0.5 ${isDue ? "text-rose-600" : "text-emerald-800"}`}>
                        {dueDateFormatted}
                      </p>
                    </div>
                  </div>

                  {/* Bottom Action */}
                  <div className="flex items-center justify-between pt-1 border-t border-stone-100">
                    <span className="text-[11px] text-stone-400 font-medium">
                      {isDue
                        ? (lang === "te" ? "ఈరోజు చేయాలి (చర్య అవసరం)" : lang === "hi" ? "आज देय (कार्रवाई आवश्यक)" : "Due today (Action needed)")
                        : (lang === "te" ? `${daysLeft} రోజులు మిగిలి ఉన్నాయి` : lang === "hi" ? `${daysLeft} दिन शेष` : `${daysLeft} days remaining`)}
                    </span>

                    <button
                      onClick={(e) => handleMarkDone(e, item.id)}
                      className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-[11px] font-bold transition active:scale-95 flex items-center gap-1 border border-emerald-200/60"
                    >
                      <Check className="size-3 stroke-[3]" />
                      <span>{isDue ? t("markDone") : (lang === "te" ? "రీసెట్ టైమర్" : lang === "hi" ? "टाइमर रीसेट" : "Reset Timer")}</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Footer Actions */}
          <div className="pt-3 border-t border-stone-100 flex items-center justify-between gap-2 text-xs">
            <button
              onClick={() => {
                setIsViewAllOpen(false);
                setIsSettingsOpen(true);
              }}
              className="text-emerald-800 font-bold hover:text-emerald-900 flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50 border border-emerald-200/80 active:scale-95 transition"
            >
              <Settings2 className="size-3.5 text-emerald-700" />
              <span>Adjust Reminder Days</span>
            </button>

            <button
              onClick={() => setIsViewAllOpen(false)}
              className="text-stone-700 font-bold hover:text-stone-900 px-3.5 py-1.5 rounded-xl border border-stone-200 active:scale-95 transition"
            >
              Close
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
