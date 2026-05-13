from __future__ import annotations
from pathlib import Path
import pandas as pd
import duckdb

def build_kpi_daily(con: duckdb.DuckDBPyConnection, sql_dir: Path) -> pd.DataFrame:
    # Ensure views exist
    con.execute((sql_dir / "10_kpi_daily.sql").read_text(encoding="utf-8"))
    df = con.execute("SELECT * FROM kpi_daily").df()
    df["ds"] = pd.to_datetime(df["ds"])
    return df
