import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export default function ScrollArea({ className, ...props }: HTMLAttributes<HTMLDivElement>): JSX.Element {
  return <div className={cn("overflow-auto", className)} {...props} />;
}

