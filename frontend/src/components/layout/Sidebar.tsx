import { LayoutDashboard, Grid3x3, Settings, ShieldAlert } from "lucide-react";
import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";

const navItems = [
  { to: "/", label: "Pulpit", icon: LayoutDashboard, end: true },
  { to: "/incidents", label: "Incydenty", icon: ShieldAlert },
  { to: "/mitre", label: "MITRE ATT&CK", icon: Grid3x3 },
  { to: "/settings", label: "Ustawienia", icon: Settings },
] as const satisfies ReadonlyArray<{
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
}>;

export default function Sidebar(): JSX.Element {
  return (
    <aside className="fixed inset-y-0 left-0 z-20 flex w-60 flex-col border-r border-border-subtle bg-bg-base">
      <div className="border-b border-border-subtle px-4 py-4">
        <div className="inline-flex flex-col">
          <span className="border-b-2 border-accent pb-1 font-mono text-[28px] font-bold leading-none tracking-[-0.04em] text-text-primary">
            FAI
          </span>
          <span className="mt-2 text-xs uppercase tracking-[0.22em] text-text-muted">Forensics AI</span>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={"end" in item ? item.end : undefined}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 border-l-2 px-3 py-2 text-sm font-medium transition-colors duration-150",
                  isActive
                    ? "border-accent bg-bg-surface-2 text-text-primary"
                    : "border-transparent text-text-secondary hover:bg-bg-surface-2 hover:text-text-primary",
                )
              }
            >
              <item.icon size={20} strokeWidth={1.5} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      <div className="border-t border-border-subtle p-4">
        <div className="flex items-center gap-3 rounded-sm border border-border-subtle bg-bg-surface px-3 py-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-accent text-xs font-semibold text-text-primary">
            MD
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-medium text-text-primary">M. Dobrowolski</div>
            <div className="truncate text-xs text-text-secondary">QA Lead · Operator</div>
          </div>
        </div>
      </div>
    </aside>
  );
}

