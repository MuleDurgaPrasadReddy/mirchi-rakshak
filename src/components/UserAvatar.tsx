import React from "react";
import { cn } from "@/lib/utils";

const AVATAR_PALETTES = [
  { bg: "#8a584c", text: "#ffffff" }, // Warm sienna / terracotta (matches sample image)
  { bg: "#166534", text: "#ffffff" }, // Deep emerald
  { bg: "#0369a1", text: "#ffffff" }, // Ocean blue
  { bg: "#6d28d9", text: "#ffffff" }, // Royal purple
  { bg: "#c2410c", text: "#ffffff" }, // Warm burnt orange
  { bg: "#047857", text: "#ffffff" }, // Rich teal
  { bg: "#991b1b", text: "#ffffff" }, // Brick red
  { bg: "#4338ca", text: "#ffffff" }, // Deep indigo
  { bg: "#be185d", text: "#ffffff" }, // Rose berry
  { bg: "#334155", text: "#ffffff" }, // Slate navy
  { bg: "#a16207", text: "#ffffff" }, // Warm bronze
  { bg: "#4d7c0f", text: "#ffffff" }, // Olive green
];

export function getAvatarColor(identifier: string) {
  let hash = 0;
  const str = (identifier || "User").toLowerCase();
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % AVATAR_PALETTES.length;
  return AVATAR_PALETTES[index];
}

interface UserAvatarProps {
  name?: string | null;
  identifier?: string | null;
  sizeClassName?: string;
  className?: string;
  fontSizeClassName?: string;
}

export function UserAvatar({
  name,
  identifier,
  sizeClassName = "size-10",
  fontSizeClassName = "text-[16px]",
  className,
}: UserAvatarProps) {
  const cleanName = (name || identifier || "User").trim();
  const initial = (cleanName[0] || "U").toUpperCase();
  const palette = getAvatarColor(cleanName);

  return (
    <div
      style={{ backgroundColor: palette.bg, color: palette.text }}
      className={cn(
        "rounded-full font-bold select-none shrink-0 grid place-items-center shadow-xs border-2 border-white ring-1 ring-black/5 transition",
        sizeClassName,
        fontSizeClassName,
        className,
      )}
    >
      <span className="leading-none">{initial}</span>
    </div>
  );
}
