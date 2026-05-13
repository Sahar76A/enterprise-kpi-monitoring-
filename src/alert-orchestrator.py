from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import ast
import pandas as pd

from .slack_formatter import format_slack_message


@dataclass
class OrchestrationResult:
    status: str
    input_alerts: int
    meaningful_alerts: int
    notifications_generated: int
    output_path: str


def _parse_detectors(value):
    if pd.isna(value):
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return ast.literal_eval(value)
        except Exception:
            return {}
    return {}


def _detector_count(detectors) -> int:
    if not isinstance(detectors, dict):
        return 0
    return sum(bool(v) for v in detectors.values())


def _is_meaningful_alert(row: pd.Series) -> bool:
    risk = str(row.get("risk_level", "")).upper()
    z = row.get("z_score")
    validation_status = str(row.get("validation_status", "")).upper()

    if validation_status == "FAIL":
        return False

    try:
        abs_z = abs(float(z))
    except (TypeError, ValueError):
        abs_z = 0.0

    if risk in {"HIGH", "MEDIUM"}:
        return True

    if abs_z >= 2.5:
        return True

    return False


def _apply_cooldown(df: pd.DataFrame, cooldown_days: int = 3) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out_rows = []
    last_sent_by_kpi: dict[str, pd.Timestamp] = {}

    df = df.sort_values(["kpi", "ds"]).copy()

    for _, row in df.iterrows():
        kpi = str(row["kpi"])
        ds = pd.to_datetime(row["ds"])
        last_sent = last_sent_by_kpi.get(kpi)

        if last_sent is None or (ds - last_sent).days >= cooldown_days:
            out_rows.append(row)
            last_sent_by_kpi[kpi] = ds

    if not out_rows:
        return df.iloc[0:0].copy()

    return pd.DataFrame(out_rows).reset_index(drop=True)


def orchestrate_alerts(
    alerts_path: str | Path,
    output_path: str | Path,
    cooldown_days: int = 3,
) -> OrchestrationResult:
    alerts_path = Path(alerts_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not alerts_path.exists():
        raise FileNotFoundError(f"Alerts file not found: {alerts_path}")

    alerts = pd.read_csv(alerts_path)
    input_alerts = len(alerts)

    if alerts.empty:
        pd.DataFrame(columns=[
            "ds", "kpi", "risk_level", "z_score", "message"
        ]).to_csv(output_path, index=False)
        return OrchestrationResult(
            status="OK",
            input_alerts=0,
            meaningful_alerts=0,
            notifications_generated=0,
            output_path=str(output_path),
        )

    alerts["ds"] = pd.to_datetime(alerts["ds"], errors="coerce")
    alerts["detectors_parsed"] = alerts["detectors"].apply(_parse_detectors)
    alerts["detector_count"] = alerts["detectors_parsed"].apply(_detector_count)

    # Keep only meaningful alerts
    filtered = alerts[alerts.apply(_is_meaningful_alert, axis=1)].copy()

    # Require at least 2 detectors for stronger signal
    filtered = filtered[filtered["detector_count"] >= 2].copy()

    meaningful_alerts = len(filtered)

    # Cooldown suppression to reduce alert fatigue
    filtered = _apply_cooldown(filtered, cooldown_days=cooldown_days)

    if filtered.empty:
        pd.DataFrame(columns=[
            "ds",
            "kpi",
            "risk_level",
            "z_score",
            "detector_count",
            "message",
        ]).to_csv(output_path, index=False)

        return OrchestrationResult(
            status="OK",
            input_alerts=input_alerts,
            meaningful_alerts=meaningful_alerts,
            notifications_generated=0,
            output_path=str(output_path),
        )

    # Sort by operational priority
    risk_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    filtered["risk_rank"] = filtered["risk_level"].astype(str).str.upper().map(risk_rank).fillna(0)
    filtered["abs_z"] = pd.to_numeric(filtered["z_score"], errors="coerce").abs()

    filtered = filtered.sort_values(
        by=["risk_rank", "abs_z", "ds"],
        ascending=[False, False, True],
    ).copy()

    # Generate Slack-style messages
    filtered["message"] = filtered.apply(lambda r: format_slack_message(r.to_dict()), axis=1)

    final_cols = [
        "ds",
        "kpi",
        "risk_level",
        "value",
        "baseline",
        "z_score",
        "detector_count",
        "validation_status",
        "injected_label",
        "message",
    ]
    final_df = filtered[final_cols].copy()
    final_df.to_csv(output_path, index=False)

    return OrchestrationResult(
        status="OK",
        input_alerts=input_alerts,
        meaningful_alerts=meaningful_alerts,
        notifications_generated=len(final_df),
        output_path=str(output_path),
    )
