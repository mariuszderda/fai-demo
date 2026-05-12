import type { TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export default function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>): JSX.Element {
  return (
    <textarea
      className={cn(
        "flex min-h-24 w-full rounded-sm border border-border-strong bg-bg-surface px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

