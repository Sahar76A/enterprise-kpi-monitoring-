from __future__ import annotations
import json
from typing import Any


def _format_currency(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _format_number(value: Any) -> str:
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _risk_emoji(risk_level: str) -> str:
    mapping = {
        "HIGH": "🔴",
        "MEDIUM": "🟠",
        "LOW": "🟡",
    }
    return mapping.get(str(risk_level).upper(), "⚪")


def _safe_root_cause_summary(root_cause_json: str | None) -> str:
    if not root_cause_json:
        return "No root cause evidence available."

    try:
        payload = json.loads(root_cause_json)
        primary_kpi = payload.get("primary_kpi", "unknown")
        evidence = payload.get("evidence", [])

        parts: list[str] = []
        for block in evidence[:2]:
            dim = block.get("dimension", "unknown_dimension")
            top = block.get("top", [])
            if not top:
                continue

            first = top[0]
            segment = first.get("segment", "unknown")
            delta = first.get("delta", 0)
            pct = first.get("pct_contrib", 0)

            try:
                delta_fmt = f"{float(delta):,.2f}"
            except (TypeError, ValueError):
                delta_fmt = "N/A"

            try:
                pct_fmt = f"{float(pct) * 100:.1f}%"
            except (TypeError, ValueError):
                pct_fmt = "N/A"

            parts.append(
                f"{dim}: top driver = {segment} (delta={delta_fmt}, contribution={pct_fmt})"
            )

        if not parts:
            return f"Primary KPI: {primary_kpi}. Root cause evidence present but not easily summarized."

        return f"Primary KPI: {primary_kpi}. " + " | ".join(parts)

    except Exception:
        return "Root cause evidence present but could not be parsed."


def format_slack_message(row: dict) -> str:
    risk = str(row.get("risk_level", "UNKNOWN")).upper()
    emoji = _risk_emoji(risk)
    ds = str(row.get("ds", "N/A"))
    kpi = str(row.get("kpi", "unknown_kpi")).replace("_", " ").title()

    value = row.get("value")
    baseline = row.get("baseline")
    z_score = row.get("z_score")
    validation_status = row.get("validation_status", "UNKNOWN")
    injected_label = row.get("injected_label")
    detectors = row.get("detectors")
    root_cause_json = row.get("root_cause_json")

    if kpi.lower() == "revenue":
        value_fmt = _format_currency(value)
        baseline_fmt = _format_currency(baseline)
    else:
        value_fmt = _format_number(value)
        baseline_fmt = _format_number(baseline)

    try:
        z_fmt = f"{float(z_score):.2f}"
    except (TypeError, ValueError):
        z_fmt = "N/A"

    detectors_text = "N/A"
    if detectors:
        detectors_text = str(detectors)

    root_cause_summary = _safe_root_cause_summary(root_cause_json)

    sim_text = ""
    if injected_label and str(injected_label).strip():
        sim_text = f"\nSimulation Tag: {injected_label}"

    message = (
        f"{emoji} *{risk} KPI Alert*\n"
        f"*Date:* {ds}\n"
        f"*KPI:* {kpi}\n"
        f"*Observed Value:* {value_fmt}\n"
        f"*Baseline:* {baseline_fmt}\n"
        f"*Z-Score:* {z_fmt}\n"
        f"*Validation Status:* {validation_status}\n"
        f"*Detectors Fired:* {detectors_text}\n"
        f"*Root Cause Summary:* {root_cause_summary}"
        f"{sim_text}"
    )

    return message
