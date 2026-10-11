export interface ReminderItem {
  id: "scan" | "spraying" | "fertilizer";
  title: string;
  subtitle: string;
  intervalDays: number;
  lastCompletedAt: string; // ISO string
  dueDate: string; // ISO string
  enabled: boolean;
}

const STORAGE_KEY = "mirchi_farm_reminders_v1";
const NOTIFICATION_STORAGE_KEY = "mirchi_reminders_last_notified";

/**
 * Returns default initial reminders with intervals:
 * - Scan: 3 days (due today)
 * - Spraying: 6 days (due in 3 days)
 * - Fertilizer: 10 days (due in 7 days)
 */
export function getDefaultReminders(): ReminderItem[] {
  const now = new Date();

  // Scan: 3 day cycle, last done 3 days ago -> due today
  const scanLast = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
  const scanDue = new Date(now.getTime());

  // Spraying: 6 day cycle, last done 3 days ago -> due in 3 days
  const sprayLast = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
  const sprayDue = new Date(now.getTime() + 3 * 24 * 60 * 60 * 1000);

  // Fertilizer: 10 day cycle, last done 3 days ago -> due in 7 days
  const fertLast = new Date(now.getTime() - 3 * 24 * 60 * 60 * 1000);
  const fertDue = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

  return [
    {
      id: "scan",
      title: "Crop scan reminder",
      subtitle: "Inspect your chilli leaves",
      intervalDays: 3,
      lastCompletedAt: scanLast.toISOString(),
      dueDate: scanDue.toISOString(),
      enabled: true,
    },
    {
      id: "spraying",
      title: "Spraying reminder",
      subtitle: "Follow your crop-protection schedule",
      intervalDays: 6,
      lastCompletedAt: sprayLast.toISOString(),
      dueDate: sprayDue.toISOString(),
      enabled: true,
    },
    {
      id: "fertilizer",
      title: "Fertilizer reminder",
      subtitle: "Apply fertilizer as per your schedule",
      intervalDays: 10,
      lastCompletedAt: fertLast.toISOString(),
      dueDate: fertDue.toISOString(),
      enabled: true,
    },
  ];
}

/**
 * Load reminders from localStorage or fallback to defaults
 */
export function loadReminders(): ReminderItem[] {
  if (typeof window === "undefined") return getDefaultReminders();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      const defaults = getDefaultReminders();
      saveReminders(defaults);
      return defaults;
    }
    const parsed = JSON.parse(raw) as ReminderItem[];
    if (!Array.isArray(parsed) || parsed.length === 0) {
      return getDefaultReminders();
    }
    return parsed;
  } catch {
    return getDefaultReminders();
  }
}

/**
 * Save reminders to localStorage
 */
export function saveReminders(items: ReminderItem[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    window.dispatchEvent(new CustomEvent("mirchi_reminders_updated"));
  } catch (err) {
    console.error("Failed to save reminders:", err);
  }
}

/**
 * Calculate days remaining until due date
 * Returns:
 * <= 0: Due today
 * 1: Tomorrow
 * > 1: In N days
 */
export function getDaysRemaining(dueDateStr: string): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);

  const due = new Date(dueDateStr);
  due.setHours(0, 0, 0, 0);

  const diffMs = due.getTime() - now.getTime();
  return Math.round(diffMs / (1000 * 60 * 60 * 24));
}

/**
 * Get formatted status pill text & style
 */
export function getReminderStatus(daysRemaining: number): {
  text: string;
  isDue: boolean;
  pillClass: string;
} {
  if (daysRemaining <= 0) {
    return {
      text: "Due today",
      isDue: true,
      pillClass: "bg-[#fee2e2] text-[#ea580c]",
    };
  }
  if (daysRemaining === 1) {
    return {
      text: "In 1 day",
      isDue: false,
      pillClass: "bg-[#dcfce7] text-[#15803d]",
    };
  }
  return {
    text: `In ${daysRemaining} days`,
    isDue: false,
    pillClass: "bg-[#dcfce7] text-[#15803d]",
  };
}

/**
 * Mark a reminder as completed today and advance its due date by its interval
 */
export function completeReminder(id: ReminderItem["id"]): ReminderItem[] {
  const current = loadReminders();
  const now = new Date();

  const updated = current.map((item) => {
    if (item.id === id) {
      const nextDue = new Date(now.getTime() + item.intervalDays * 24 * 60 * 60 * 1000);
      return {
        ...item,
        lastCompletedAt: now.toISOString(),
        dueDate: nextDue.toISOString(),
      };
    }
    return item;
  });

  saveReminders(updated);
  return updated;
}

/**
 * Update intervals set by the user and recompute upcoming due dates
 */
export function updateReminderIntervals(intervals: {
  scan: number;
  spraying: number;
  fertilizer: number;
}): ReminderItem[] {
  const current = loadReminders();
  const now = new Date();

  const updated = current.map((item) => {
    const newInterval = Math.max(1, intervals[item.id] ?? item.intervalDays);
    const lastDone = new Date(item.lastCompletedAt || now.toISOString());
    const nextDue = new Date(lastDone.getTime() + newInterval * 24 * 60 * 60 * 1000);

    return {
      ...item,
      intervalDays: newInterval,
      dueDate: nextDue.toISOString(),
    };
  });

  saveReminders(updated);
  return updated;
}

/**
 * Request browser push/desktop notification permission
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (typeof window === "undefined" || !("Notification" in window)) {
    return "denied";
  }
  return await Notification.requestPermission();
}

/**
 * Trigger browser notification for due tasks (rate-limited per calendar day)
 */
export function triggerBrowserNotificationIfDue(items: ReminderItem[]): void {
  if (typeof window === "undefined" || !("Notification" in window)) return;
  if (Notification.permission !== "granted") return;

  const todayStr = new Date().toDateString();
  const lastNotified = localStorage.getItem(NOTIFICATION_STORAGE_KEY);
  if (lastNotified === todayStr) return; // Already reminded today

  const dueTasks = items.filter((i) => i.enabled && getDaysRemaining(i.dueDate) <= 0);
  if (dueTasks.length === 0) return;

  const titles = dueTasks.map((t) => t.title).join(", ");
  try {
    new Notification("🌱 Mirchi Rakshak Farm Reminder", {
      body: `You have ${dueTasks.length} task(s) due today: ${titles}. Tap to view your crop health.`,
      icon: "/favicon.ico",
      tag: "mirchi-farm-reminder",
    });
    localStorage.setItem(NOTIFICATION_STORAGE_KEY, todayStr);
  } catch (err) {
    console.error("Browser notification failed:", err);
  }
}
