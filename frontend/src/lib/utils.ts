import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

import type { Severity } from "./types";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatUtcAsLocal(iso: string): string {
  const date = new Date(iso);
  return new Intl.DateTimeFormat("sv-SE", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

export function formatDurationMs(ms: number): string {
  if (!Number.isFinite(ms)) {
    return "—";
  }
  const whole = Math.max(0, Math.round(ms));
  if (whole < 1000) {
    return `${whole}ms`;
  }
  const totalSeconds = Math.round(whole / 100) / 10;
  if (totalSeconds < 60) {
    return `${totalSeconds.toFixed(totalSeconds < 10 ? 1 : 0)}s`;
  }
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.round(totalSeconds % 60);
  if (minutes < 60) {
    return `${minutes}m ${seconds}s`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

export function truncateMiddle(value: string, length = 12): string {
  if (value.length <= length || length <= 3) {
    return value;
  }
  const prefix = Math.ceil((length - 1) / 2);
  const suffix = Math.floor((length - 1) / 2);
  return `${value.slice(0, prefix)}…${value.slice(value.length - suffix)}`;
}

export function severityColor(severity: Severity | string): string {
  switch (severity) {
    case "critical":
      return "text-severity-critical border-severity-critical";
    case "high":
      return "text-severity-high border-severity-high";
    case "medium":
      return "text-severity-medium border-severity-medium";
    case "low":
      return "text-severity-low border-severity-low";
    case "info":
      return "text-severity-info border-severity-info";
    default:
      return "text-text-secondary border-border-subtle";
  }
}

