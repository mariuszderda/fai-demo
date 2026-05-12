import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "outline" | "destructive";
}

const variantClasses: Record<NonNullable<BadgeProps["variant"]>, string> = {
  default: "border-accent bg-accent text-bg-base",
  secondary: "border-border-strong bg-bg-surface-2 text-text-primary",
  outline: "border-border-strong bg-transparent text-text-primary",
  destructive: "border-severity-critical bg-severity-critical text-bg-base",
};

export default function Badge({ className, variant = "outline", ...props }: BadgeProps): JSX.Element {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-sm border px-2 py-0.5 text-xs font-medium leading-none",
        variantClasses[variant],
        className,
      )}
      {...props}
    />
  );
}

