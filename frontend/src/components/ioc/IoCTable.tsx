import type { IoC } from "@/lib/types";
import { truncateMiddle } from "@/lib/utils";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import Badge from "@/components/ui/badge";
import IoCBadge from "@/components/ioc/IoCBadge";

export default function IoCTable({ iocs }: { iocs: IoC[] }): JSX.Element {
  return (
    <div className="rounded-sm border border-border-subtle bg-bg-surface">
      <Table>
        <TableHeader>
          <tr>
            <TableHead>Typ</TableHead>
            <TableHead>Wartość</TableHead>
            <TableHead>Pewność</TableHead>
            <TableHead>Reputacja</TableHead>
            <TableHead>MITRE</TableHead>
          </tr>
        </TableHeader>
        <TableBody>
          {iocs.map((ioc) => (
            <TableRow key={ioc.id}>
              <TableCell><IoCBadge type={ioc.type} /></TableCell>
              <TableCell className="font-mono" title={ioc.value}>{truncateMiddle(ioc.value, 42)}</TableCell>
              <TableCell>
                <Badge variant="outline" className={ioc.confidence === "high" ? "border-accent text-accent" : ioc.confidence === "medium" ? "border-severity-info text-severity-info" : "text-text-muted"}>
                  {ioc.confidence}
                </Badge>
              </TableCell>
              <TableCell>{ioc.reputation ?? "—"}</TableCell>
              <TableCell className="font-mono text-xs">{ioc.mitre_technique_ids.join(", ") || "—"}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

