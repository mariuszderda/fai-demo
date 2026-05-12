import type { IocType } from "@/lib/types";
import Badge from "@/components/ui/badge";

const TYPE_LABEL: Record<IocType, string> = {
  ipv4: "IP",
  ipv6: "IP",
  domain: "DOM",
  url: "URL",
  md5: "HASH",
  sha1: "HASH",
  sha256: "HASH",
  file_path: "PATH",
  email: "EMAIL",
};

export default function IoCBadge({ type }: { type: IocType }): JSX.Element {
  return <Badge className="border-border-strong bg-bg-surface-2 font-mono text-[11px]">{TYPE_LABEL[type]}</Badge>;
}

