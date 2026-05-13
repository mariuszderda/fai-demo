import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import Button from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "@/components/ui/toast";

interface ApprovalCardState {
  currentIndex: number;
  secondsLeft: number;
}

export default function ApprovalCard(): JSX.Element | null {
  const queryClient = useQueryClient();
  const [state, setState] = useState<ApprovalCardState>({ currentIndex: 0, secondsLeft: 0 });
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState<"APPROVE" | "DENY" | "KILLSWITCH" | null>(null);

  const approvalsQuery = useQuery({
    queryKey: ["approvals"],
    queryFn: api.listPendingApprovals,
    refetchInterval: 2000,
  });

  const decideMutation = useMutation({
    mutationFn: (decision: "APPROVE" | "DENY" | "KILLSWITCH") => {
      const approval = approvals[state.currentIndex];
      if (!approval) throw new Error("No approval selected");
      return api.decideApproval(approval.id, decision, "M. Dobrowolski");
    },
    onSuccess: () => {
      setConfirmOpen(false);
      setConfirmAction(null);
      void queryClient.invalidateQueries({ queryKey: ["approvals"] });
      void queryClient.invalidateQueries({ queryKey: ["incident"] });
    },
    onError: (err) => {
      toast({ title: "Nie udało się wysłać decyzji", description: (err as Error).message, variant: "destructive" });
    },
  });

  const approvals = approvalsQuery.data ?? [];
  const currentApproval = approvals[state.currentIndex];

  // Update seconds left countdown
  useEffect(() => {
    if (!currentApproval) return;

    const ttl = currentApproval.ttl_seconds;
    const createdAt = new Date(currentApproval.created_at_utc).getTime();
    const now = Date.now();
    const elapsed = Math.floor((now - createdAt) / 1000);
    const left = Math.max(0, ttl - elapsed);

    setState((prev) => ({ ...prev, secondsLeft: left }));

    if (left === 0) {
      // Expire
      setConfirmOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["approvals"] });
      return;
    }

    const timer = setInterval(() => {
      setState((prev) => {
        const next = prev.secondsLeft - 1;
        if (next < 0) {
          clearInterval(timer);
          void queryClient.invalidateQueries({ queryKey: ["approvals"] });
          return prev;
        }
        return { ...prev, secondsLeft: next };
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [currentApproval, queryClient]);

  // Handle keyboard shortcuts
  useEffect(() => {
    if (!currentApproval || confirmOpen) return;

    const handleKeyDown = (e: KeyboardEvent): void => {
      if (e.key.toLowerCase() === "a") {
        setConfirmAction("APPROVE");
        setConfirmOpen(true);
      } else if (e.key.toLowerCase() === "d") {
        setConfirmAction("DENY");
        setConfirmOpen(true);
      } else if (e.key.toLowerCase() === "k") {
        setConfirmAction("KILLSWITCH");
        setConfirmOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentApproval, confirmOpen]);

  if (!currentApproval) {
    return null;
  }

  const minutes = Math.floor(state.secondsLeft / 60);
  const seconds = state.secondsLeft % 60;
  const countdownClass = state.secondsLeft < 60 ? "text-severity-critical" : "text-text-primary";

  return (
    <>
      <div className="fixed bottom-4 right-4 z-40 pointer-events-auto animate-in slide-in-from-right-10 duration-300">
        <div className={`w-[360px] rounded-sm border-2 bg-bg-elevated p-4 ${state.secondsLeft < 60 ? "border-severity-critical" : "border-severity-high"}`}>
          <div className="mb-3">
            <div className="font-mono text-[13px] font-semibold">Wymagana zgoda · Izolacja hosta</div>
            {approvals.length > 1 ? <div className="text-[11px] text-text-secondary">{state.currentIndex + 1} z {approvals.length}</div> : null}
          </div>

          <div className="space-y-2 mb-4 text-sm">
            <div>
              <div className="text-text-secondary text-xs">Host ID</div>
              <div className="font-mono">{currentApproval.host_id}</div>
            </div>
            <div>
              <div className="text-text-secondary text-xs">Powód</div>
              <div>{currentApproval.reason}</div>
            </div>
            <div>
              <div className="text-text-secondary text-xs">Cel</div>
              <div className="text-xs">
                {currentApproval.isolation_target === "host_network" ? "Sieć hosta" : "Kwarantanna mail relay"}
              </div>
            </div>
            <div>
              <div className={`font-mono text-[28px] ${countdownClass}`}>
                {String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
              </div>
            </div>
          </div>

          <div className="flex gap-2 mb-2">
            <Button
              size="sm"
              className="flex-1"
              onClick={() => {
                setConfirmAction("APPROVE");
                setConfirmOpen(true);
              }}
              disabled={decideMutation.status === "pending"}
              aria-label="APPROVE (A)"
            >
              APPROVE
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="flex-1"
              onClick={() => {
                setConfirmAction("DENY");
                setConfirmOpen(true);
              }}
              disabled={decideMutation.status === "pending"}
              aria-label="DENY (D)"
            >
              DENY
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="flex-1 border-severity-critical text-severity-critical hover:bg-severity-critical/10"
              onClick={() => {
                setConfirmAction("KILLSWITCH");
                setConfirmOpen(true);
              }}
              disabled={decideMutation.status === "pending"}
              aria-label="KILLSWITCH (K)"
            >
              K-SWITCH
            </Button>
          </div>

          {approvals.length > 1 ? (
            <div className="flex gap-2 text-xs text-text-secondary">
              <button
                className="px-2 py-1 border border-border-subtle rounded-sm hover:bg-bg-surface transition-colors"
                onClick={() => setState((prev) => ({ ...prev, currentIndex: Math.max(0, prev.currentIndex - 1) }))}
                disabled={state.currentIndex === 0}
              >
                ← Poprzednia
              </button>
              <button
                className="px-2 py-1 border border-border-subtle rounded-sm hover:bg-bg-surface transition-colors"
                onClick={() => setState((prev) => ({ ...prev, currentIndex: Math.min(approvals.length - 1, prev.currentIndex + 1) }))}
                disabled={state.currentIndex === approvals.length - 1}
              >
                Następna →
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Potwierdź decyzję</DialogTitle>
            <DialogDescription>
              {confirmAction === "APPROVE"
                ? "Zatwierdzasz izolację hosta. Procedura będzie wykonana natychmiast."
                : confirmAction === "DENY"
                  ? "Odrzucasz wniosek o izolację. System wznowi pracę bez izolacji."
                  : "Aktywujesz kill-switch. Incydent zostanie wstrzymany do przeglądu."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 text-sm">
            <div>
              <div className="text-text-secondary">Host ID</div>
              <div className="font-mono">{currentApproval.host_id}</div>
            </div>
            <div>
              <div className="text-text-secondary">Powód</div>
              <div>{currentApproval.reason}</div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)} disabled={decideMutation.status === "pending"}>
              Anuluj
            </Button>
            <Button
              onClick={() => {
                if (confirmAction) {
                  decideMutation.mutate(confirmAction);
                }
              }}
              disabled={decideMutation.status === "pending"}
              className={confirmAction === "KILLSWITCH" ? "border-severity-critical text-severity-critical" : ""}
            >
              Potwierdź
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

