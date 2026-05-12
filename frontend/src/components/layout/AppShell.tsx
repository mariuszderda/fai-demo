import { Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { formatUtcAsLocal, truncateMiddle } from "@/lib/utils";

import Card, { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Badge from "@/components/ui/badge";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function PendingApprovalsCard(): JSX.Element | null {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["approvals"],
    queryFn: api.listPendingApprovals,
    refetchInterval: 15_000,
  });

  return (
    <Card className="pointer-events-auto w-[20rem] shadow-none">
      <CardHeader className="gap-2 border-b border-border-subtle pb-3">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-sm">Oczekujące zgody</CardTitle>
          <Badge variant="outline">{data?.length ?? 0}</Badge>
        </div>
      </CardHeader>
      <CardContent className="p-3 text-sm text-text-secondary">
        {isLoading ? <div>Ładowanie…</div> : null}
        {isError ? <div>Nie udało się pobrać zgód.</div> : null}
        {!isLoading && !isError && (data?.length ?? 0) === 0 ? <div>Brak oczekujących zgód.</div> : null}
        {!isLoading && !isError && (data?.length ?? 0) > 0 ? (
          <div className="space-y-3">
            {data?.slice(0, 2).map((approval) => (
              <div key={approval.id} className="rounded-sm border border-border-subtle bg-bg-surface p-2 text-xs text-text-secondary">
                <div className="flex items-center justify-between gap-2 text-text-primary">
                  <span>{truncateMiddle(approval.id, 14)}</span>
                  <span>{approval.ttl_seconds}s</span>
                </div>
                <div className="mt-1">{approval.host_id}</div>
                <div className="mt-1">{formatUtcAsLocal(approval.created_at_utc)}</div>
              </div>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

export default function AppShell(): JSX.Element {
  return (
    <div className="min-h-screen bg-bg-base text-text-primary">
      <Sidebar />
      <Topbar />
      <main className="min-h-screen pl-60 pt-12">
        <div className="min-h-[calc(100vh-3rem)] px-4 py-4">
          <Outlet />
        </div>
      </main>
      <div className="pointer-events-none fixed bottom-4 right-4 z-20">
        <PendingApprovalsCard />
      </div>
    </div>
  );
}

