import { createContext, useContext, useMemo, useState } from "react";
import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

interface SheetContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const SheetContext = createContext<SheetContextValue | null>(null);

export interface SheetProps {
  children: ReactNode;
  defaultOpen?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function Sheet({ children, defaultOpen = false, open, onOpenChange }: SheetProps): JSX.Element {
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const isControlled = open !== undefined;
  const actualOpen = isControlled ? open : internalOpen;
  const setOpen = useMemo(
    () => (next: boolean) => {
      if (!isControlled) {
        setInternalOpen(next);
      }
      onOpenChange?.(next);
    },
    [isControlled, onOpenChange],
  );

  return <SheetContext.Provider value={{ open: actualOpen, setOpen }}>{children}</SheetContext.Provider>;
}

export interface SheetTriggerProps {
  children: ReactNode;
}

export function SheetTrigger({ children }: SheetTriggerProps): JSX.Element {
  const context = useContext(SheetContext);
  if (context === null) {
    throw new Error("SheetTrigger must be used inside Sheet");
  }
  return (
    <span onClick={() => context.setOpen(true)}>
      {children}
    </span>
  );
}

export interface SheetContentProps extends HTMLAttributes<HTMLDivElement> {
  side?: "right" | "left";
}

export function SheetContent({ className, side = "right", children, ...props }: SheetContentProps): JSX.Element | null {
  const context = useContext(SheetContext);
  if (context === null) {
    throw new Error("SheetContent must be used inside Sheet");
  }
  if (!context.open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex">
      <button
        type="button"
        className="absolute inset-0 cursor-default bg-black/70"
        aria-label="Zamknij panel boczny"
        onClick={() => context.setOpen(false)}
      />
      <div
        className={cn(
          "relative z-10 h-full w-80 border-l border-border-subtle bg-bg-elevated p-4 text-text-primary shadow-none",
          side === "left" && "border-l-0 border-r",
          side === "right" ? "ml-auto" : "mr-auto",
          className,
        )}
        {...props}
      >
        {children}
      </div>
    </div>
  );
}

export function SheetHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("flex flex-col gap-1.5", className)} {...props} />;
}

export function SheetTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>): JSX.Element {
  return <h3 className={cn("text-base font-semibold text-text-primary", className)} {...props} />;
}

export function SheetDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>): JSX.Element {
  return <p className={cn("text-sm text-text-secondary", className)} {...props} />;
}

