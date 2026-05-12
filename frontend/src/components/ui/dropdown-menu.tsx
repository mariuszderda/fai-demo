import { createContext, useContext, useMemo, useState } from "react";
import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

interface DropdownContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const DropdownContext = createContext<DropdownContextValue | null>(null);

export function DropdownMenu({ children }: { children: ReactNode }): JSX.Element {
  const [open, setOpen] = useState(false);
  const value = useMemo(() => ({ open, setOpen }), [open]);
  return <DropdownContext.Provider value={value}>{children}</DropdownContext.Provider>;
}

export function DropdownMenuTrigger({ children }: { children: ReactNode }): JSX.Element {
  const context = useContext(DropdownContext);
  if (context === null) {
    throw new Error("DropdownMenuTrigger must be used inside DropdownMenu");
  }
  return (
    <span onClick={() => context.setOpen(!context.open)}>
      {children}
    </span>
  );
}

export function DropdownMenuContent({ className, children, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element | null {
  const context = useContext(DropdownContext);
  if (context === null || !context.open) {
    return null;
  }
  return (
    <div
      className={cn(
        "absolute right-0 z-50 mt-2 w-56 rounded-sm border border-border-subtle bg-bg-elevated p-1 text-text-primary",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function DropdownMenuItem({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  const context = useContext(DropdownContext);
  return (
    <div
      className={cn("cursor-pointer rounded-sm px-2 py-1.5 text-sm text-text-primary hover:bg-bg-surface-2", className)}
      onClick={() => context?.setOpen(false)}
      {...props}
    />
  );
}

export function DropdownMenuSeparator({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("my-1 h-px bg-border-subtle", className)} {...props} />;
}

