import { createContext, useContext, useMemo, useState } from "react";
import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

interface TooltipContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const TooltipContext = createContext<TooltipContextValue | null>(null);

export function TooltipProvider({ children }: { children: ReactNode }): JSX.Element {
  return <>{children}</>;
}

export function Tooltip({ children }: { children: ReactNode }): JSX.Element {
  const [open, setOpen] = useState(false);
  const value = useMemo(() => ({ open, setOpen }), [open]);
  return (
    <TooltipContext.Provider value={value}>
      <span className="relative inline-flex">{children}</span>
    </TooltipContext.Provider>
  );
}

export function TooltipTrigger({ children }: { children: ReactNode }): JSX.Element {
  const context = useContext(TooltipContext);
  if (context === null) {
    throw new Error("TooltipTrigger must be used inside Tooltip");
  }
  return (
    <span
      onMouseEnter={() => context.setOpen(true)}
      onMouseLeave={() => context.setOpen(false)}
      onFocus={() => context.setOpen(true)}
      onBlur={() => context.setOpen(false)}
    >
      {children}
    </span>
  );
}

export interface TooltipContentProps extends HTMLAttributes<HTMLDivElement> {}

export function TooltipContent({ className, children, ...props }: TooltipContentProps): JSX.Element | null {
  const context = useContext(TooltipContext);
  if (context === null || !context.open) {
    return null;
  }
  return (
    <div
      className={cn(
        "absolute left-1/2 top-full z-50 mt-2 -translate-x-1/2 whitespace-nowrap rounded-sm border border-border-subtle bg-bg-elevated px-2 py-1 text-xs text-text-primary",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

