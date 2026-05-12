import { createContext, useContext, useMemo, useState } from "react";
import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/lib/utils";

interface DialogContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const DialogContext = createContext<DialogContextValue | null>(null);

export interface DialogProps {
  children: ReactNode;
  defaultOpen?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function Dialog({ children, defaultOpen = false, open, onOpenChange }: DialogProps): JSX.Element {
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

  return <DialogContext.Provider value={{ open: actualOpen, setOpen }}>{children}</DialogContext.Provider>;
}

export interface DialogTriggerProps {
  children: ReactNode;
}

export function DialogTrigger({ children }: DialogTriggerProps): JSX.Element {
  const context = useContext(DialogContext);
  if (context === null) {
    throw new Error("DialogTrigger must be used inside Dialog");
  }
  return (
    <span onClick={() => context.setOpen(true)}>
      {children}
    </span>
  );
}

export interface DialogContentProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function DialogContent({ className, children, ...props }: DialogContentProps): JSX.Element | null {
  const context = useContext(DialogContext);
  if (context === null) {
    throw new Error("DialogContent must be used inside Dialog");
  }
  if (!context.open) {
    return null;
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 cursor-default bg-black/70"
        aria-label="Zamknij okno dialogowe"
        onClick={() => context.setOpen(false)}
      />
      <div
        className={cn("relative z-10 w-full max-w-lg rounded-sm border border-border-subtle bg-bg-elevated p-4 text-text-primary", className)}
        {...props}
      >
        {children}
      </div>
    </div>
  );
}

export function DialogHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("flex flex-col gap-1.5", className)} {...props} />;
}

export function DialogTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>): JSX.Element {
  return <h3 className={cn("text-base font-semibold text-text-primary", className)} {...props} />;
}

export function DialogDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>): JSX.Element {
  return <p className={cn("text-sm text-text-secondary", className)} {...props} />;
}

export function DialogFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("mt-4 flex justify-end gap-2", className)} {...props} />;
}

