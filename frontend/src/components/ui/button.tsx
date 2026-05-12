import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type ButtonVariant = "default" | "secondary" | "outline" | "ghost" | "destructive";
type ButtonSize = "sm" | "default" | "lg" | "icon";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

const variantClasses: Record<ButtonVariant, string> = {
  default: "border-accent bg-accent text-bg-base hover:bg-accent-dim hover:border-accent-dim",
  secondary: "border-border-strong bg-bg-surface-2 text-text-primary hover:bg-bg-elevated",
  outline: "border-border-strong bg-transparent text-text-primary hover:bg-bg-surface-2",
  ghost: "border-transparent bg-transparent text-text-primary hover:bg-bg-surface-2",
  destructive: "border-severity-critical bg-severity-critical text-bg-base hover:opacity-90",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-xs",
  default: "h-9 px-4 text-sm",
  lg: "h-10 px-5 text-sm",
  icon: "h-9 w-9",
};

export default function Button({ className, variant = "default", size = "default", type = "button", ...props }: ButtonProps): JSX.Element {
  return (
    <button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-sm border font-medium transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    />
  );
}

