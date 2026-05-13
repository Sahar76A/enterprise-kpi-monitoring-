from __future__ import annotations
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

def detect_anomalies(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    out = df.copy()
    min_days = int(cfg["baseline"]["min_days_for_detection"])

    # Initialize columns
    for kpi in cfg["kpis"]:
        out[f"{kpi}_anomaly_rule"] = False
        out[f"{kpi}_anomaly_z"] = False
        out[f"{kpi}_anomaly_iqr"] = False
        out[f"{kpi}_anomaly_iforest"] = False
        out[f"{kpi}_anomaly_flag"] = False

    # Heuristic + Z + IQR
    pct = float(cfg["anomaly_detection"]["heuristic_pct_dev"])
    zt = float(cfg["anomaly_detection"]["zscore_threshold"])

    for kpi in cfg["kpis"]:
        base_col = f"{kpi}_base{int(cfg['baseline']['baseline_days'])}"
        dev = (out[kpi] - out[base_col]) / out[base_col].replace(0, np.nan)

        out.loc[:, f"{kpi}_anomaly_rule"] = dev.abs() > pct
        out.loc[:, f"{kpi}_anomaly_z"] = out[f"{kpi}_z"].abs() > zt
        out.loc[:, f"{kpi}_anomaly_iqr"] = (out[kpi] < out[f"{kpi}_iqr_lo"]) | (out[kpi] > out[f"{kpi}_iqr_hi"])

    # Isolation Forest as detector #3 (supporting evidence)
    if cfg["anomaly_detection"]["isolation_forest"]["enabled"]:
        iso_cfg = cfg["anomaly_detection"]["isolation_forest"]
        features = []
        for kpi in cfg["kpis"]:
            features.append(kpi)
        X = out[features].astype(float).copy()

        # Handle early NaNs by forward fill then back fill (monitoring systems often do this for detectors)
        X = X.ffill().bfill()

        model = IsolationForest(
            n_estimators=int(iso_cfg["n_estimators"]),
            contamination=float(iso_cfg["contamination"]),
            random_state=int(iso_cfg["random_state"]),
        )
        pred = model.fit_predict(X)  # -1 anomalous, 1 normal

        # Apply IF signal only after minimum history exists (governance)
        out["_iforest_flag"] = (pred == -1)
        out.loc[out.index < min_days, "_iforest_flag"] = False

        # Attach IF signal to each KPI (same day-level detector)
        for kpi in cfg["kpis"]:
            out[f"{kpi}_anomaly_iforest"] = out["_iforest_flag"]

        out.drop(columns=["_iforest_flag"], inplace=True)

    # Final anomaly flag: require at least 2 detectors firing (reduces alert fatigue)
    for kpi in cfg["kpis"]:
        votes = (
            out[f"{kpi}_anomaly_z"].astype(int)
            + out[f"{kpi}_anomaly_iqr"].astype(int)
            + out[f"{kpi}_anomaly_iforest"].astype(int)
            + out[f"{kpi}_anomaly_rule"].astype(int)
        )
        out[f"{kpi}_anomaly_flag"] = votes >= 2

        # Don’t alert in cold start period
        out.loc[out.index < min_days, f"{kpi}_anomaly_flag"] = False

    return out
