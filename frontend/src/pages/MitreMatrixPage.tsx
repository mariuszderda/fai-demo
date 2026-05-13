import MitreMatrix from "@/components/mitre/MitreMatrix";

export default function MitreMatrixPage(): JSX.Element {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="font-mono text-[28px] tracking-[-0.03em] text-text-primary">MITRE ATT&CK · Globalne pokrycie</h1>
        <div className="text-sm text-text-secondary">Przegląd wszystkich zdetektowanych technik w obecnej sesji.</div>
      </div>
      <MitreMatrix global />
    </div>
  );
}

