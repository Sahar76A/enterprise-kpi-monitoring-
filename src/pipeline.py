from __future__ import annotations
from pathlib import Path
import pandas as pd

from .config import Config
from .io_duckdb import connect, run_sql_file
from .kpi_builder import build_kpi_daily
from .data_validation import validate_kpi_frame, validation_report_to_df
from .anomaly_injection import inject_anomalies
from .baseline_engine import add_rolling_stats
from .anomaly_engine import detect_anomalies
from .risk_engine import classify_risk
from .root_cause_engine import attach_root_cause

def run_pipeline(conf: Config) -> dict:
    conf.outputs_dir.mkdir(parents=True, exist_ok=True)

    # 1) Load raw → DuckDB staging
    con = connect(conf.warehouse_path)

    raw = conf.raw_dir
    files = {
        "orders_csv": raw / "olist_orders_dataset.csv",
        "order_items_csv": raw / "olist_order_items_dataset.csv",
        "products_csv": raw / "olist_products_dataset.csv",
        "customers_csv": raw / "olist_customers_dataset.csv",
        "payments_csv": raw / "olist_order_payments_dataset.csv",
    }
    missing = [k for k, p in files.items() if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing raw CSVs: {missing}. Put Kaggle Olist CSVs in {raw}."
        )

    run_sql_file(con, Path("sql/00_create_staging.sql"), {k: str(v) for k, v in files.items()})

    # 2) Build KPI daily mart
    df = build_kpi_daily(con, Path("sql"))

    # 3) Inject anomalies (controlled)
    df = inject_anomalies(df, conf.cfg)

    # 4) Validation gate
    # Governance rule: if FAIL, still export report, but stop anomaly pipeline.
    vr = validate_kpi_frame(df)
    dq_df = validation_report_to_df(vr)
    dq_path = conf.outputs_dir / "data_quality_report.csv"
    dq_df.to_csv(dq_path, index=False)

    kpi_path = conf.outputs_dir / "kpi_daily.csv"
    df.to_csv(kpi_path, index=False)

    if vr.status == "FAIL":
        return {
            "status": "STOPPED_DATA_QUALITY_FAIL",
            "kpi_daily_path": str(kpi_path),
            "data_quality_report_path": str(dq_path),
            "alerts_path": None,
        }

    # 5) Baselines + rolling stats
    df2 = add_rolling_stats(df, conf.cfg)

    # 6) Multi-method anomaly detection
    df3 = detect_anomalies(df2, conf.cfg)

    # 7) Risk classification + escalation logic
    df4 = classify_risk(df3, conf.cfg)

    # 8) Root cause attribution (evidence artifact)
    df5 = attach_root_cause(con, df4, conf.cfg)

    # 9) Build alert table (operator-ready)
    alert_rows = []
    for _, row in df5.iterrows():
        ds = row["ds"]
        for kpi in conf.cfg["kpis"]:
            if bool(row.get(f"{kpi}_anomaly_flag", False)):
                alert_rows.append({
                    "ds": ds,
                    "kpi": kpi,
                    "value": float(row[kpi]) if pd.notna(row[kpi]) else None,
                    "baseline": float(row.get(f"{kpi}_base{int(conf.cfg['baseline']['baseline_days'])}", float("nan")))
                                if pd.notna(row.get(f"{kpi}_base{int(conf.cfg['baseline']['baseline_days'])}", None)) else None,
                    "z_score": float(row.get(f"{kpi}_z", float("nan"))) if pd.notna(row.get(f"{kpi}_z", None)) else None,
                    "risk_level": row.get(f"{kpi}_risk_level", "NONE"),
                    "detectors": {
                        "rule": bool(row.get(f"{kpi}_anomaly_rule", False)),
                        "z": bool(row.get(f"{kpi}_anomaly_z", False)),
                        "iqr": bool(row.get(f"{kpi}_anomaly_iqr", False)),
                        "iforest": bool(row.get(f"{kpi}_anomaly_iforest", False)),
                    },
                    "root_cause_json": row.get("root_cause_json", None),
                    "validation_status": vr.status,
                    "injected_label": row.get("injected_label", None),
                })

    alerts = pd.DataFrame(alert_rows)
    alerts_path = conf.outputs_dir / "alerts.csv"
    alerts.to_csv(alerts_path, index=False)

    return {
        "status": "OK",
        "kpi_daily_path": str(kpi_path),
        "data_quality_report_path": str(dq_path),
        "alerts_path": str(alerts_path),
    }
