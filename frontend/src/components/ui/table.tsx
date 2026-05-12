import type { HTMLAttributes, TableHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Table({ className, ...props }: TableHTMLAttributes<HTMLTableElement>): JSX.Element {
  return <table className={cn("w-full caption-bottom text-sm", className)} {...props} />;
}

export function TableHeader({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>): JSX.Element {
  return <thead className={cn("[&_tr]:border-b", className)} {...props} />;
}

export function TableBody({ className, ...props }: HTMLAttributes<HTMLTableSectionElement>): JSX.Element {
  return <tbody className={cn("[&_tr:last-child]:border-0", className)} {...props} />;
}

export function TableRow({ className, ...props }: HTMLAttributes<HTMLTableRowElement>): JSX.Element {
  return <tr className={cn("border-b border-border-subtle transition-colors hover:bg-bg-surface-2", className)} {...props} />;
}

export function TableHead({ className, ...props }: HTMLAttributes<HTMLTableCellElement>): JSX.Element {
  return <th className={cn("h-10 px-3 text-left align-middle font-medium text-text-secondary", className)} {...props} />;
}

export function TableCell({ className, ...props }: HTMLAttributes<HTMLTableCellElement>): JSX.Element {
  return <td className={cn("p-3 align-middle text-text-primary", className)} {...props} />;
}

export function TableCaption({ className, ...props }: HTMLAttributes<HTMLTableCaptionElement>): JSX.Element {
  return <caption className={cn("mt-4 text-sm text-text-muted", className)} {...props} />;
}

