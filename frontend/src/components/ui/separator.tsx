import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export interface SeparatorProps extends HTMLAttributes<HTMLDivElement> {
  orientation?: "horizontal" | "vertical";
}

export default function Separator({ className, orientation = "horizontal", ...props }: SeparatorProps): JSX.Element {
  return (
    <div
      role="separator"
      aria-orientation={orientation}
      className={cn(
        orientation === "horizontal" ? "h-px w-full" : "h-full w-px",
        "bg-border-subtle",
        className,
      )}
      {...props}
    />
  );
}

