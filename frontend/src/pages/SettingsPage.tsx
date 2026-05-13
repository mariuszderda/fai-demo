import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import Card, { CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Badge from "@/components/ui/badge";

export default function SettingsPage(): JSX.Element {
  const settingsQuery = useQuery({ queryKey: ["settings"], queryFn: api.getSettings });

  if (settingsQuery.isLoading) {
    return <div className="rounded-sm border border-border-subtle bg-bg-surface p-4 text-sm text-text-secondary">Ładowanie ustawień…</div>;
  }

  if (settingsQuery.isError || !settingsQuery.data) {
    return <div className="rounded-sm border border-severity-critical bg-bg-surface p-4 text-sm">Nie udało się pobrać ustawień.</div>;
  }

  const settings = settingsQuery.data;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-mono text-[28px] tracking-[-0.03em] text-text-primary">Ustawienia</h1>
        <div className="text-sm text-text-secondary">Konfiguracja systemu (tylko do odczytu).</div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>LLM</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-text-secondary">Provider:</div>
            <div>{settings.llm.provider}</div>
            <div className="text-text-secondary">Model:</div>
            <div className="font-mono">{settings.llm.model}</div>
            <div className="text-text-secondary">Status:</div>
            <div>
              {settings.llm.stub_active ? (
                <Badge className="border-severity-high bg-severity-high/10 text-severity-high">Tryb stub aktywny</Badge>
              ) : (
                <Badge className="border-accent bg-accent/10 text-accent">Rzeczywisty LLM</Badge>
              )}
            </div>
          </div>
          {settings.llm.stub_active ? (
            <div className="rounded-sm border border-severity-high bg-severity-high/5 p-2 text-xs text-severity-high">
              Wywoływania LLM zwracają predefiniowane dane. Skonfiguruj ANTHROPIC_API_KEY, aby włączyć rzeczywiste wywołania.
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Threat Intelligence</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-text-secondary">OTX API:</div>
            <div>{settings.otx.key_present ? <Badge className="border-accent bg-accent/10 text-accent">Dostępny</Badge> : <Badge className="border-border-strong bg-bg-surface-2">Niedostępny</Badge>}</div>
          </div>
          {!settings.otx.key_present ? <div className="rounded-sm border border-severity-medium bg-severity-medium/5 p-2 text-xs text-severity-medium">Brak klucza OTX — używany fallback z lokalnego MISP.</div> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>MITRE ATT&CK</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-text-secondary">Wersja:</div>
            <div>{settings.mitre.version}</div>
            <div className="text-text-secondary">Liczba technik:</div>
            <div>{settings.mitre.techniques_count.toLocaleString()}</div>
            <div className="text-text-secondary">Ścieżka:</div>
            <div className="font-mono text-xs">{settings.mitre.path}</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Zatwierdzenia & Izolacja</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-text-secondary">TTL na zatwierdzenie:</div>
            <div>{settings.approval_ttl_seconds} sekund</div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Katalogi czasu wykonania</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2 text-xs">
            <div>
              <div className="text-text-secondary">Audyt:</div>
              <div className="font-mono">{settings.directories.audit}</div>
            </div>
            <div>
              <div className="text-text-secondary">Artefakty:</div>
              <div className="font-mono">{settings.directories.artifacts}</div>
            </div>
            <div>
              <div className="text-text-secondary">Raporty:</div>
              <div className="font-mono">{settings.directories.reports}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

