import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export default function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>): JSX.Element {
  return (
    <input
      className={cn(
        "flex h-9 w-full rounded-sm border border-border-strong bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

