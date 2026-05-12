import type { HTMLAttributes, ReactNode } from "react";

import { cn, severityColor } from "@/lib/utils";

import Badge from "./badge";

export interface SeverityBadgeProps extends HTMLAttributes<HTMLDivElement> {
  severity: "critical" | "high" | "medium" | "low" | "info";
  children: ReactNode;
}

export default function SeverityBadge({ severity, className, children, ...props }: SeverityBadgeProps): JSX.Element {
  return (
    <Badge
      variant="outline"
      className={cn("border px-2 py-0.5", severityColor(severity), className)}
      {...props}
    >
      {children}
    </Badge>
  );
}

export { SeverityBadge as Badge };

