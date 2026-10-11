import { useState, useEffect, useCallback } from "react";
import { supabase } from "@/integrations/supabase/client";

export interface UserLocation {
  district: string;
  state: string;
  country: string;
  lat: number;
  lon: number;
  source: "gps" | "ip" | "cached" | "default";
}

export const DEFAULT_LOCATION: UserLocation = {
  district: "Guntur",
  state: "Andhra Pradesh",
  country: "India",
  lat: 16.3067,
  lon: 80.4365,
  source: "default",
};

const STORAGE_KEY = "mr_detected_location";
const LOCATION_EVENT = "mr-location-updated";

/** Read synchronous cached location from localStorage to avoid initial render flashes */
export function getCachedLocation(): UserLocation {
  if (typeof window === "undefined") return DEFAULT_LOCATION;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed.district === "string" && typeof parsed.lat === "number") {
        return { ...parsed, source: "cached" };
      }
    }
  } catch (err) {
    console.warn("Failed reading cached location:", err);
  }
  return DEFAULT_LOCATION;
}

/** Get GPS coordinates via HTML5 Geolocation */
function getGpsCoordinates(): Promise<{ lat: number; lon: number } | null> {
  return new Promise((resolve) => {
    if (typeof window === "undefined" || !navigator.geolocation) {
      resolve(null);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        resolve({
          lat: Number(pos.coords.latitude.toFixed(4)),
          lon: Number(pos.coords.longitude.toFixed(4)),
        });
      },
      (err) => {
        console.info("GPS geolocation unavailable or denied, falling back to IP:", err.message);
        resolve(null);
      },
      {
        enableHighAccuracy: true,
        timeout: 6000,
        maximumAge: 1000 * 60 * 15, // 15 mins cache
      },
    );
  });
}

/** Reverse geocode coordinates or fallback to IP lookup using BigDataCloud Client API */
export async function detectUserLocation(): Promise<UserLocation> {
  try {
    // 1. Try browser GPS first
    const gps = await getGpsCoordinates();

    const url = gps
      ? `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${gps.lat}&longitude=${gps.lon}&localityLanguage=en`
      : `https://api.bigdatacloud.net/data/reverse-geocode-client?localityLanguage=en`;

    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(`Geocoding HTTP ${res.status}`);

    const data = await res.json();

    // Determine district / city name
    const rawCity =
      data.city ||
      data.locality ||
      data.localityInfo?.administrative?.[2]?.name ||
      data.localityInfo?.administrative?.[1]?.name ||
      "";

    // Clean up city string (e.g. remove "District" suffix if present)
    const district = rawCity ? rawCity.replace(/\s+District$/i, "").trim() : "Guntur";
    const state = data.principalSubdivision || "Andhra Pradesh";
    const country = data.countryName || "India";
    const lat = typeof data.latitude === "number" ? Number(data.latitude.toFixed(4)) : (gps?.lat ?? DEFAULT_LOCATION.lat);
    const lon = typeof data.longitude === "number" ? Number(data.longitude.toFixed(4)) : (gps?.lon ?? DEFAULT_LOCATION.lon);

    const detected: UserLocation = {
      district: district || DEFAULT_LOCATION.district,
      state: state || DEFAULT_LOCATION.state,
      country: country || DEFAULT_LOCATION.country,
      lat,
      lon,
      source: gps ? "gps" : "ip",
    };

    // Cache to localStorage
    if (typeof window !== "undefined") {
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(detected));
        window.dispatchEvent(new CustomEvent(LOCATION_EVENT, { detail: detected }));
      } catch (e) {
        console.warn("Could not save detected location:", e);
      }
    }

    // Optionally sync with Supabase profiles table if user is logged in
    try {
      const { data: authData } = await supabase.auth.getUser();
      if (authData?.user) {
        await supabase
          .from("profiles")
          .update({ district: detected.district })
          .eq("id", authData.user.id);
      }
    } catch {
      // Non-blocking sync
    }

    return detected;
  } catch (err) {
    console.warn("Location detection error, using cached/default:", err);
    return getCachedLocation();
  }
}

/** Hook to automatically access and keep user location up to date */
export function useUserLocation() {
  const [location, setLocation] = useState<UserLocation>(getCachedLocation);
  const [isLoading, setIsLoading] = useState(false);

  const refreshLocation = useCallback(async () => {
    setIsLoading(true);
    try {
      const detected = await detectUserLocation();
      setLocation(detected);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Initial fetch on mount
    refreshLocation();

    // Listen for updates across components or tabs
    const handleUpdate = (e: Event) => {
      const detail = (e as CustomEvent<UserLocation>).detail;
      if (detail) setLocation(detail);
    };

    window.addEventListener(LOCATION_EVENT, handleUpdate);
    return () => window.removeEventListener(LOCATION_EVENT, handleUpdate);
  }, [refreshLocation]);

  return { location, isLoading, refreshLocation };
}
