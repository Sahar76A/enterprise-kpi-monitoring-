from __future__ import annotations
import json
from dataclasses import dataclass
import pandas as pd
import duckdb

@dataclass
class RootCauseResult:
    dimension: str
    top_contributors: list[dict]

def _segment_contribution(
    con: duckdb.DuckDBPyConnection,
    ds: str,
    kpi: str,
    dim: str,
    lookback_days: int,
) -> RootCauseResult:
    # Compare segment revenue (or orders) vs baseline mean over lookback window
    metric_expr = "SUM(price + freight_value)" if kpi == "revenue" else "COUNT(DISTINCT order_id)"
    where_delivered = "order_status = 'delivered'"

    q = f"""
    WITH daily_seg AS (
      SELECT
        purchase_date AS ds,
        {dim} AS segment,
        {metric_expr} AS metric
      FROM mart_order_facts
      WHERE {where_delivered}
      GROUP BY 1,2
    ),
    baseline AS (
      SELECT
        segment,
        AVG(metric) AS base_metric
      FROM daily_seg
      WHERE ds < DATE '{ds}'
        AND ds >= DATE '{ds}' - INTERVAL '{lookback_days} days'
      GROUP BY 1
    ),
    today AS (
      SELECT segment, metric AS today_metric
      FROM daily_seg
      WHERE ds = DATE '{ds}'
    ),
    joined AS (
      SELECT
        COALESCE(t.segment, b.segment) AS segment,
        COALESCE(t.today_metric, 0) AS today_metric,
        COALESCE(b.base_metric, 0) AS base_metric,
        (COALESCE(t.today_metric, 0) - COALESCE(b.base_metric, 0)) AS delta
      FROM today t
      FULL OUTER JOIN baseline b USING(segment)
    )
    SELECT *
    FROM joined
    ORDER BY ABS(delta) DESC
    LIMIT 50;
    """
    seg = con.execute(q).df()
    if seg.empty:
        return RootCauseResult(dim, [])

    total_delta = float(seg["delta"].sum()) if seg["delta"].notna().any() else 0.0
    if total_delta == 0:
        total_delta = 1e-9

    seg["pct_contrib"] = seg["delta"] / total_delta

    # Top drivers by absolute contribution
    seg = seg.sort_values("pct_contrib", key=lambda s: s.abs(), ascending=False)

    top = []
    for _, row in seg.head(5).iterrows():
        top.append({
            "segment": None if pd.isna(row["segment"]) else str(row["segment"]),
            "today": float(row["today_metric"]),
            "baseline": float(row["base_metric"]),
            "delta": float(row["delta"]),
            "pct_contrib": float(row["pct_contrib"]),
        })
    return RootCauseResult(dim, top)

def attach_root_cause(
    con: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    cfg: dict,
) -> pd.DataFrame:
    out = df.copy()
    dims = cfg["root_cause"]["dimensions"]
    lookback = int(cfg["root_cause"]["lookback_days"])
    top_n = int(cfg["root_cause"]["top_n"])

    out["root_cause_json"] = None

    # Only compute for anomaly days (any KPI)
    anomaly_days = out[
        out[[f"{k}_anomaly_flag" for k in cfg["kpis"]]].any(axis=1)
    ].copy()

    if anomaly_days.empty:
        return out

    for idx, row in anomaly_days.iterrows():
        ds = row["ds"].date().isoformat()

        # Pick the “primary” KPI of that day: highest risk severity, tie-break by abs(z)
        def sev_score(k: str) -> int:
            lvl = row[f"{k}_risk_level"]
            return {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}.get(lvl, 0)

        primary = sorted(
            cfg["kpis"],
            key=lambda k: (sev_score(k), abs(row.get(f"{k}_z", 0.0))),
            reverse=True,
        )[0]

        results = []
        for dim in dims:
            rc = _segment_contribution(con, ds=ds, kpi=primary, dim=dim, lookback_days=lookback)
            results.append({
                "dimension": rc.dimension,
                "top": rc.top_contributors[:top_n],
            })

        out.at[idx, "root_cause_json"] = json.dumps({
            "primary_kpi": primary,
            "evidence": results,
        }, ensure_ascii=False)

    return out
