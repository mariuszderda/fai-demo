import { useSyncExternalStore } from "react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export interface ToastOptions {
  title: string;
  description?: string;
  variant?: "default" | "destructive";
  action?: ReactNode;
  durationMs?: number;
}

interface ToastState extends ToastOptions {
  id: string;
}

type Subscriber = () => void;

const toasts = new Map<string, ToastState>();
const subscribers = new Set<Subscriber>();
let cachedSnapshot: ToastState[] = [];

function updateSnapshot(): void {
  // Keep snapshot reference stable between renders unless store state changed.
  cachedSnapshot = Array.from(toasts.values());
}

function emit(): void {
  for (const subscriber of subscribers) {
    subscriber();
  }
}

function subscribe(subscriber: Subscriber): () => void {
  subscribers.add(subscriber);
  return () => {
    subscribers.delete(subscriber);
  };
}

function snapshot(): ToastState[] {
  return cachedSnapshot;
}

export function toast(options: ToastOptions): string {
  const id = globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  toasts.set(id, { id, ...options });
  updateSnapshot();
  emit();
  const duration = options.durationMs ?? 5000;
  globalThis.setTimeout(() => {
    if (toasts.delete(id)) {
      updateSnapshot();
      emit();
    }
  }, duration);
  return id;
}

function dismiss(id: string): void {
  if (toasts.delete(id)) {
    updateSnapshot();
    emit();
  }
}

export function useToasts(): ToastState[] {
  return useSyncExternalStore(subscribe, snapshot, snapshot);
}

export function Toaster(): JSX.Element {
  const items = useToasts();
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-[22rem] flex-col gap-2">
      {items.map((item) => (
        <div
          key={item.id}
          className={cn(
            "pointer-events-auto rounded-sm border border-border-subtle bg-bg-elevated p-3 text-text-primary",
            item.variant === "destructive" && "border-severity-critical",
          )}
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-sm font-semibold">{item.title}</div>
              {item.description ? <div className="mt-1 text-xs text-text-secondary">{item.description}</div> : null}
            </div>
            <button
              type="button"
              className="text-text-muted transition-colors duration-150 hover:text-text-primary"
              onClick={() => dismiss(item.id)}
              aria-label="Zamknij powiadomienie"
            >
              ×
            </button>
          </div>
          {item.action ? <div className="mt-3">{item.action}</div> : null}
        </div>
      ))}
    </div>
  );
}

