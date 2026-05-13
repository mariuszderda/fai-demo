import { useMemo } from "react";

import Input from "@/components/ui/input";
import { AUDIT_LABELS } from "@/lib/labels";

interface Filters {
  action: string;
  actor: string;
  since: string;
}

interface AuditFilterProps {
  filters: Filters;
  setFilters: (filters: Filters) => void;
}

export default function AuditFilter({ filters, setFilters }: AuditFilterProps): JSX.Element {
  const uniqueActions = useMemo(() => {
    return Object.keys(AUDIT_LABELS).sort();
  }, []);

  return (
    <div className="flex flex-wrap gap-2 rounded-sm border border-border-subtle bg-bg-surface p-3">
      <div className="w-full">
        <label className="block text-xs text-text-secondary mb-1">Akcja</label>
        <select
          className="w-full h-20 rounded-sm border border-border-strong bg-bg-surface-2 p-2 text-xs"
          value={filters.action}
          onChange={(e) => {
            setFilters({ ...filters, action: e.target.value });
          }}
        >
          <option value="">— wszystkie —</option>
          {uniqueActions.map((action) => (
            <option key={action} value={action}>
              {AUDIT_LABELS[action] ?? action}
            </option>
          ))}
        </select>
      </div>

      <Input
        placeholder="Aktor (np. M. Dobrowolski)"
        className="text-xs"
        value={filters.actor}
        onChange={(e) => setFilters({ ...filters, actor: e.target.value })}
      />

      <Input
        placeholder="Od (ISO 8601)"
        className="text-xs"
        type="date"
        value={filters.since}
        onChange={(e) => setFilters({ ...filters, since: e.target.value })}
      />
    </div>
  );
}

