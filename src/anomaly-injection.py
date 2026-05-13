from __future__ import annotations
import pandas as pd
import numpy as np


def inject_anomalies(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    inj = cfg.get("anomaly_injection", {})
    out = df.copy()

    if not inj.get("enabled", False):
        out["injected_label"] = None
        return out

    out["injected_label"] = None
    seed = int(inj.get("seed", 42))
    rng = np.random.default_rng(seed)

    # Ensure deterministic ordering
    out = out.sort_values("ds").reset_index(drop=True)

    # Make KPI columns float before applying multiplicative anomalies
    for kpi in cfg.get("kpis", []):
        if kpi in out.columns:
            out[kpi] = pd.to_numeric(out[kpi], errors="coerce").astype(float)

    for e in inj.get("events", []):
        kpi = e["kpi"]
        start = pd.to_datetime(e["start_date"])
        days = int(e["days"])
        mult = float(e["multiplier"])
        label = str(e.get("label", "Injected anomaly"))

        mask = (out["ds"] >= start) & (out["ds"] < start + pd.Timedelta(days=days))
        if kpi in out.columns and mask.any():
            noise = rng.normal(loc=1.0, scale=0.01, size=int(mask.sum()))
            out.loc[mask, kpi] = out.loc[mask, kpi] * mult * noise
            out.loc[mask, "injected_label"] = label

    return out
