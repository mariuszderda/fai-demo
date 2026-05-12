import { ChevronRight } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import Badge from "@/components/ui/badge";
import { api } from "@/lib/api";
import { useAnyIncidentStreamConnected } from "@/lib/sse";
import { cn } from "@/lib/utils";

interface Crumb {
  label: string;
}

function breadcrumbs(pathname: string): Crumb[] {
  if (pathname === "/") {
    return [{ label: "Pulpit" }];
  }
  if (pathname === "/incidents") {
    return [{ label: "Incydenty" }];
  }
  if (pathname.startsWith("/incidents/")) {
    return [{ label: "Incydenty" }, { label: "Szczegóły incydentu" }];
  }
  if (pathname === "/mitre") {
    return [{ label: "MITRE ATT&CK" }];
  }
  if (pathname === "/settings") {
    return [{ label: "Ustawienia" }];
  }
  if (pathname === "/_probe") {
    return [{ label: "Probe interfejsu" }];
  }
  return [{ label: "FAI" }];
}

export default function Topbar(): JSX.Element {
  const { pathname } = useLocation();
  const connected = useAnyIncidentStreamConnected();
  const { data: settings } = useQuery({
    queryKey: ["settings"],
    queryFn: api.getSettings,
  });

  const crumbs = breadcrumbs(pathname);

  return (
    <header className="fixed left-0 top-0 z-10 h-12 w-full border-b border-border-subtle bg-bg-base/95 pl-60 backdrop-blur-0">
      <div className="flex h-full items-center justify-between gap-4 px-4">
        <nav aria-label="Okruszki" className="flex min-w-0 items-center gap-2 text-xs text-text-secondary">
          {crumbs.map((crumb, index) => (
            <div key={`${crumb.label}-${index}`} className="flex min-w-0 items-center gap-2">
              {index > 0 ? <ChevronRight size={14} strokeWidth={1.5} className="text-text-muted" /> : null}
              <span className={cn(index === crumbs.length - 1 ? "text-text-primary" : "truncate")}>{crumb.label}</span>
            </div>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-sm border border-border-subtle bg-bg-surface px-2 py-1 text-xs text-text-secondary">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                connected ? "bg-emerald-500" : "bg-text-muted",
              )}
              aria-hidden="true"
            />
            <span>{connected ? "SSE aktywne" : "SSE nieaktywne"}</span>
          </div>
          {settings?.llm.stub_active ? <Badge variant="outline">Tryb stub LLM</Badge> : null}
        </div>
      </div>
    </header>
  );
}

