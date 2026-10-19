export interface ScanRecord {
  id: string;
  user_id?: string | null;
  image_url?: string | null;
  disease: string;
  confidence?: number;
  severity?: string;
  affected_area?: string;
  risk_level?: string;
  recommendation?: string;
  treatment?: Array<{ step: string; detail: string }> | Record<string, unknown> | null;
  recovery_days?: number;
  is_healthy?: boolean;
  is_chili_leaf?: boolean;
  invalid_reason?: string | null;
  language?: string;
  created_at: string;
}

const STORAGE_KEY = "mr-scan-history";

export const BASELINE_SCAN: ScanRecord = {
  id: "scan-baseline-01",
  disease: "Healthy Chili Plant",
  confidence: 0.95,
  severity: "None",
  affected_area: "0%",
  risk_level: "Low",
  recommendation: "Leaves look normal & healthy, flowering stage progressing well.",
  treatment: [
    { step: "Maintain irrigation", detail: "Regular drip irrigation at 3-day intervals" },
    { step: "Balanced nutrition", detail: "Foliar application of micronutrients" },
  ],
  recovery_days: 0,
  is_healthy: true,
  is_chili_leaf: true,
  language: "en",
  created_at: "2026-10-08T10:24:00.000Z",
};

/**
 * Loads scans from localStorage. If no scans have been recorded yet, initializes
 * with the baseline field scan.
 */
export function loadLocalScans(): ScanRecord[] {
  if (typeof window === "undefined") return [BASELINE_SCAN];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      saveLocalScans([BASELINE_SCAN]);
      return [BASELINE_SCAN];
    }
    const parsed = JSON.parse(raw) as ScanRecord[];
    if (!Array.isArray(parsed) || parsed.length === 0) {
      saveLocalScans([BASELINE_SCAN]);
      return [BASELINE_SCAN];
    }
    return parsed.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  } catch (err) {
    console.warn("Failed to load local scans:", err);
    return [BASELINE_SCAN];
  }
}

/**
 * Saves a list of scans to localStorage and dispatches an update event.
 */
export function saveLocalScans(items: ScanRecord[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    window.dispatchEvent(new CustomEvent("mirchi_scans_updated"));
  } catch (err) {
    console.error("Failed to save local scans:", err);
  }
}

/**
 * Adds a new scan to the beginning of the list, updates localStorage, and notifies listeners.
 */
export function recordNewScan(newScan: ScanRecord): void {
  const current = loadLocalScans();
  const existingIdx = current.findIndex((s) => s.id === newScan.id);
  let updated: ScanRecord[];
  if (existingIdx >= 0) {
    updated = [...current];
    updated[existingIdx] = newScan;
  } else {
    updated = [newScan, ...current];
  }
  // Keep up to 50 most recent scans
  updated = updated
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 50);
  saveLocalScans(updated);
}

/**
 * Formats a scan date into localized day-month-year representation
 */
export function formatScanDate(isoString?: string | null, lang: string = "en"): string {
  if (!isoString) return "8 Oct 2026";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return "8 Oct 2026";
    return d.toLocaleDateString(
      lang === "te" ? "te-IN" : lang === "hi" ? "hi-IN" : "en-GB",
      {
        day: "numeric",
        month: "short",
        year: "numeric",
      }
    );
  } catch {
    return "8 Oct 2026";
  }
}

/**
 * Formats a scan date with full date and time (e.g. '19 Oct 2026, 10:24 AM')
 */
export function formatScanDateTime(isoString?: string | null): string {
  if (!isoString) return "10 Oct 2026, 10:24 AM";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return "10 Oct 2026, 10:24 AM";
    const day = d.getDate();
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const month = months[d.getMonth()];
    const year = d.getFullYear();
    const hours = d.getHours();
    const mins = d.getMinutes().toString().padStart(2, "0");
    const ampm = hours >= 12 ? "PM" : "AM";
    const formattedHours = hours % 12 || 12;
    return `${day} ${month} ${year}, ${formattedHours}:${mins} ${ampm}`;
  } catch {
    return "10 Oct 2026, 10:24 AM";
  }
}
