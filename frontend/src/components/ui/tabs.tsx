import { createContext, useContext, useState } from "react";
import type { ButtonHTMLAttributes, HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

interface TabsContextValue {
  value: string;
  setValue: (value: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

export interface TabsProps extends HTMLAttributes<HTMLDivElement> {
  defaultValue: string;
}

export function Tabs({ defaultValue, className, children, ...props }: TabsProps): JSX.Element {
  const [value, setValue] = useState(defaultValue);
  return (
    <TabsContext.Provider value={{ value, setValue }}>
      <div className={cn("w-full", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
}

export function TabsList({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("inline-flex h-9 items-center rounded-sm border border-border-subtle bg-bg-surface-2 p-1", className)} {...props} />;
}

export interface TabsTriggerProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

export function TabsTrigger({ value, className, type = "button", ...props }: TabsTriggerProps): JSX.Element {
  const context = useContext(TabsContext);
  if (context === null) {
    throw new Error("TabsTrigger must be used inside Tabs");
  }
  const active = context.value === value;
  return (
    <button
      type={type}
      onClick={() => context.setValue(value)}
      className={cn(
        "inline-flex h-7 items-center justify-center rounded-sm border px-3 text-xs font-medium transition-colors duration-150",
        active
          ? "border-accent bg-bg-elevated text-text-primary"
          : "border-transparent bg-transparent text-text-secondary hover:bg-bg-surface hover:text-text-primary",
        className,
      )}
      {...props}
    />
  );
}

export interface TabsContentProps extends HTMLAttributes<HTMLDivElement> {
  value: string;
}

export function TabsContent({ value, className, ...props }: TabsContentProps): JSX.Element | null {
  const context = useContext(TabsContext);
  if (context === null) {
    throw new Error("TabsContent must be used inside Tabs");
  }
  if (context.value !== value) {
    return null;
  }
  return <div className={cn("mt-4", className)} {...props} />;
}

