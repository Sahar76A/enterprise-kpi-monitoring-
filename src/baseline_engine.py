from __future__ import annotations
import pandas as pd
import numpy as np

def add_rolling_stats(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    b = cfg["baseline"]
    rm = int(b["rolling_mean_days"])
    rs = int(b["rolling_std_days"])
    base = int(b["baseline_days"])

    out = df.sort_values("ds").copy()

    for kpi in cfg["kpis"]:
        s = out[kpi].astype(float)

        out[f"{kpi}_rm{rm}"] = s.rolling(rm, min_periods=rm).mean()
        out[f"{kpi}_rs{rs}"] = s.rolling(rs, min_periods=rs).std(ddof=0)

        out[f"{kpi}_base{base}"] = s.rolling(base, min_periods=base).mean()

        denom = out[f"{kpi}_rs{rs}"].replace(0, np.nan)
        out[f"{kpi}_z"] = (s - out[f"{kpi}_rm{rm}"]) / denom

        # IQR bounds on a rolling baseline window
        q1 = s.rolling(base, min_periods=base).quantile(0.25)
        q3 = s.rolling(base, min_periods=base).quantile(0.75)
        iqr = (q3 - q1)
        k = float(cfg["anomaly_detection"]["iqr_k"])
        out[f"{kpi}_iqr_lo"] = q1 - k * iqr
        out[f"{kpi}_iqr_hi"] = q3 + k * iqr

    return out
