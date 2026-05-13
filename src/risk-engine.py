from __future__ import annotations
import pandas as pd
import numpy as np

def classify_risk(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    out = df.copy()
    r = cfg["risk"]
    z_low = float(r["z_low"])
    z_med = float(r["z_medium"])
    z_high = float(r["z_high"])
    rev_escalate = float(r["revenue_drop_escalate_pct"])

    for kpi in cfg["kpis"]:
        out[f"{kpi}_risk_level"] = "NONE"

        z = out[f"{kpi}_z"].abs()
        out.loc[z >= z_low, f"{kpi}_risk_level"] = "LOW"
        out.loc[z >= z_med, f"{kpi}_risk_level"] = "MEDIUM"
        out.loc[z >= z_high, f"{kpi}_risk_level"] = "HIGH"

        # Only meaningful if anomaly flag is true
        out.loc[~out[f"{kpi}_anomaly_flag"], f"{kpi}_risk_level"] = "NONE"

    # Business escalation rule: revenue drop > 30% => HIGH
    kpi = "revenue"
    base_col = f"{kpi}_base{int(cfg['baseline']['baseline_days'])}"
    dev = (out[kpi] - out[base_col]) / out[base_col].replace(0, np.nan)
    big_drop = dev <= -rev_escalate
    out.loc[big_drop & out[f"{kpi}_anomaly_flag"], f"{kpi}_risk_level"] = "HIGH"

    return out
