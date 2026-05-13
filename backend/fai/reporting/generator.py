"""Report generation with LLM-powered executive summaries."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from markdown_it import MarkdownIt

from fai.analysis.llm_client import LlmClient, LlmResponseError
from fai.analysis.prompts import (
    SYSTEM_PROMPT_EXECUTIVE_SUMMARY,
    build_executive_summary_user_content,
)
from fai.core.audit import AuditTrail
from fai.core.models import Artifact, Incident, IoC, IocStatus

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate incident reports with executive summaries."""

    def __init__(
        self,
        llm_client: LlmClient,
        audit: AuditTrail,
        runtime_dir: Path,
        templates_dir: Path | None = None,
    ) -> None:
        """Initialize report generator.

        Args:
            llm_client: LLM client for executive summary.
            audit: Audit trail for reading events.
            runtime_dir: Runtime directory for output.
            templates_dir: Directory containing Jinja2 templates.
        """
        self.llm = llm_client
        self.audit = audit
        self.runtime_dir = Path(runtime_dir)

        # Setup templates directory
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates"
        self.templates_dir = Path(templates_dir)

        # Setup Jinja2
        if self.templates_dir.exists():
            self.env = Environment(loader=FileSystemLoader(self.templates_dir))
        else:
            self.env = None

    async def generate(
        self,
        incident: Incident,
        iocs: list[IoC],
        artifacts: list[Artifact],
    ) -> tuple[str, str]:
        """Generate full incident report.

        Args:
            incident: Incident data.
            iocs: List of IoCs extracted.
            artifacts: List of artifacts analyzed.

        Returns:
            Tuple of (markdown_content, html_content).
        """
        # Create reports dir
        reports_dir = self.runtime_dir / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        # Build report data structure
        report_data = self._build_report_data(incident, iocs, artifacts)

        # Get executive summary from LLM
        try:
            executive_summary = await self._generate_executive_summary(incident.id, report_data)
        except LlmResponseError as e:
            logger.error(f"Failed to generate executive summary: {e}")
            executive_summary = "Failed to generate summary due to LLM error.\n"

        # Read audit trail
        audit_events = await self.audit.read(incident.id)

        # Build markdown content
        markdown_content = self._build_markdown(
            incident=incident,
            executive_summary=executive_summary,
            audit_events=audit_events,
            iocs=iocs,
            artifacts=artifacts,
        )

        # Convert to HTML
        html_content = self._markdown_to_html(markdown_content)

        # Write files
        md_path = reports_dir / f"{incident.id}.md"
        html_path = reports_dir / f"{incident.id}.html"

        md_path.write_text(markdown_content, encoding="utf-8")
        html_path.write_text(html_content, encoding="utf-8")

        logger.info(f"Report generated: {md_path}")

        return markdown_content, html_content

    def _build_report_data(
        self, incident: Incident, iocs: list[IoC], artifacts: list[Artifact]
    ) -> dict[str, Any]:
        """Build structured report data for LLM."""
        return {
            "incident_id": incident.id,
            "scenario": incident.scenario,
            "severity": incident.severity.value,
            "started_at_utc": incident.started_at_utc.isoformat(),
            "completed_at_utc": incident.completed_at_utc.isoformat() if incident.completed_at_utc else None,
            "ioc_count": len(iocs),
            "artifact_count": len(artifacts),
            "iocs": [
                {
                    "value": ioc.value,
                    "type": ioc.type.value,
                    "confidence": ioc.confidence.value,
                    "reputation": ioc.reputation.value if ioc.reputation else None,
                    "techniques": ioc.mitre_technique_ids,
                }
                for ioc in iocs if ioc.status == IocStatus.ACCEPTED
            ],
            "artifacts": [
                {
                    "filename": a.filename,
                    "source": a.source,
                    "size_bytes": a.size_bytes,
                    "sha256": a.sha256,
                }
                for a in artifacts
            ],
        }
    async def _generate_executive_summary(
            self,
            incident_id: str,
            report_data: dict[str, Any],
    ) -> str:
        """Generate executive summary using LLM."""
        user_content = build_executive_summary_user_content(report_data)
        try:
            response = await self.llm.complete_json(
                SYSTEM_PROMPT_EXECUTIVE_SUMMARY,
                user_content,
                incident_id=incident_id,
            )
            if isinstance(response, str):
                return response
            if isinstance(response, dict):
                for key in ("executive_summary", "summary", "content", "text", "markdown"):
                    if key in response and isinstance(response[key], str):
                        return response[key]
                strs = [v for v in response.values() if isinstance(v, str) and len(v) > 50]
                if strs:
                    return max(strs, key=len)
            return str(response)
        except Exception:
            # LLM returned plain markdown instead of JSON — that's fine
            # Try to get raw text from the last API call
            try:
                raw = await self.llm.complete_raw(
                    SYSTEM_PROMPT_EXECUTIVE_SUMMARY,
                    user_content,
                    incident_id=incident_id,
                )
                return raw
            except Exception:
                raise
    # async def _generate_executive_summary(
    #     self,
    #     incident_id: str,
    #     report_data: dict[str, Any],
    # ) -> str:
    #     """Generate executive summary using LLM.
    #
    #     Args:
    #         report_data: Structured incident data.
    #
    #     Returns:
    #         Polish Markdown summary text.
    #     """
    #     user_content = build_executive_summary_user_content(report_data)
    #
    #     response = await self.llm.complete_json(
    #         SYSTEM_PROMPT_EXECUTIVE_SUMMARY,
    #         user_content,
    #         incident_id=incident_id,
    #     )
    #
    #     # Extract text (could be plain text or wrapped in a field)
    #     if isinstance(response, dict):
    #         # summary = response.get("summary", str(response))
    #         for _k in ("executive_summary", "summary", "content", "text", "markdown"):
    #             if _k in response and isinstance(response[_k], str):
    #                 summary = response[_k]
    #                 break
    #         else:
    #             _strs = [v for v in response.values() if isinstance(v, str) and len(v) > 50]
    #             summary = max(_strs, key=len) if _strs else str(response)
    #     else:
    #         summary = str(response)
    #
    #     return summary

    def _build_markdown(
        self,
        incident: Incident,
        executive_summary: str,
        audit_events: list[Any],  # AuditEvent objects
        iocs: list[IoC],
        artifacts: list[Artifact],
    ) -> str:
        """Build full markdown report.

        Args:
            incident: Incident data.
            executive_summary: LLM-generated summary.
            audit_events: Audit trail events.
            iocs: IoCs extracted.
            artifacts: Artifacts analyzed.

        Returns:
            Full markdown report.
        """
        lines: list[str] = []

        # Title
        lines.append(f"# Raport incydentu: {incident.id}\n")
        lines.append(f"**Scenariusz:** {incident.scenario}\n")
        lines.append(f"**Ważność:** {incident.severity.value}\n")
        lines.append(f"**Data startu:** {incident.started_at_utc.isoformat()}\n")
        lines.append("")

        # Executive Summary Section
        lines.append("## Streszczenie wykonawcze\n")
        lines.append(executive_summary)
        lines.append("")

        # Timeline Section
        lines.append("## Oś czasu\n")
        lines.append("| Czas (UTC) | Akcja | Szczegóły |\n")
        lines.append("|---|---|---|\n")

        for event in audit_events:
            time_str = event.ts_utc.isoformat() if hasattr(event, "ts_utc") else ""
            action = event.action if hasattr(event, "action") else ""
            details = event.object if hasattr(event, "object") else ""
            lines.append(f"| {time_str} | {action} | {details} |\n")

        lines.append("")

        # IoC Table Section
        lines.append("## Wskaźniki kompromisu (zaakceptowane)\n")
        lines.append("| Typ | Wartość | Reputacja | Źródło | Techniki MITRE |\n")
        lines.append("|---|---|---|---|---|\n")

        for ioc in iocs:
            if ioc.status != IocStatus.ACCEPTED:
                continue

            rep = ioc.reputation.value if ioc.reputation else "unknown"
            source = ioc.reputation_source or ""
            techniques = ", ".join(ioc.mitre_technique_ids) or "—"

            lines.append(f"| {ioc.type.value} | {ioc.value} | {rep} | {source} | {techniques} |\n")

        lines.append("")

        # Chain of Custody Section
        lines.append("## Łańcuch nadzoru\n")
        lines.append(f"**Liczba artefaktów:** {len(artifacts)}\n")
        lines.append("\n**Skróty SHA-256:**\n")
        for artifact in artifacts:
            lines.append(f"- {artifact.filename}: `{artifact.sha256}`\n")

        return "".join(lines)

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML.

        Args:
            markdown: Markdown text.

        Returns:
            HTML content.
        """
        # Setup markdown-it (without plugins for simplicity)
        md = MarkdownIt("commonmark")

        html = md.render(markdown)

        # Wrap in basic HTML document
        full_html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raport incydentu</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1, h2, h3 {{
            color: #1a1a1a;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin: 10px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>"""

        return full_html

