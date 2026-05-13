from __future__ import annotations
import pandas as pd
from dataclasses import dataclass

@dataclass
class ValidationResult:
    status: str  # PASS / WARN / FAIL
    issues: list[dict]

def validate_kpi_frame(df: pd.DataFrame) -> ValidationResult:
    issues: list[dict] = []

    required_cols = {"ds", "revenue", "orders", "aov", "payment_fail_rate"}
    missing = required_cols - set(df.columns)
    if missing:
        issues.append({"check": "schema_required_cols", "severity": "FAIL", "detail": f"Missing: {sorted(missing)}"})

    if "ds" in df.columns:
        if df["ds"].isna().any():
            issues.append({"check": "ds_nulls", "severity": "FAIL", "detail": "ds contains nulls"})
        if df["ds"].duplicated().any():
            dup_ct = int(df["ds"].duplicated().sum())
            issues.append({"check": "ds_duplicates", "severity": "FAIL", "detail": f"{dup_ct} duplicate dates"})

    # sanity checks
    if "revenue" in df.columns:
        neg = df["revenue"].fillna(0) < 0
        if neg.any():
            issues.append({"check": "revenue_negative", "severity": "FAIL", "detail": f"{int(neg.sum())} days with revenue < 0"})

    if "orders" in df.columns:
        neg = df["orders"].fillna(0) < 0
        if neg.any():
            issues.append({"check": "orders_negative", "severity": "FAIL", "detail": f"{int(neg.sum())} days with orders < 0"})

    # null rate thresholds (governance)
    for col in ["revenue", "orders", "aov", "payment_fail_rate"]:
        if col in df.columns:
            null_rate = float(df[col].isna().mean())
            if null_rate > 0.02:
                issues.append({"check": f"null_rate_{col}", "severity": "WARN", "detail": f"{col} null rate = {null_rate:.2%}"})

    # gap detection in dates
    if "ds" in df.columns and pd.api.types.is_datetime64_any_dtype(df["ds"]):
        s = df.sort_values("ds")["ds"].dropna().unique()
        if len(s) >= 2:
            diffs = pd.Series(s[1:]) - pd.Series(s[:-1])
            gap_days = diffs.dt.days.max()
            if gap_days and gap_days > 2:
                issues.append({"check": "date_gaps", "severity": "WARN", "detail": f"Max gap between dates = {gap_days} days"})

    status = "PASS"
    if any(i["severity"] == "FAIL" for i in issues):
        status = "FAIL"
    elif any(i["severity"] == "WARN" for i in issues):
        status = "WARN"

    return ValidationResult(status=status, issues=issues)

def validation_report_to_df(result: ValidationResult) -> pd.DataFrame:
    if not result.issues:
        return pd.DataFrame([{"check": "all", "severity": "PASS", "detail": "No issues detected"}])
    return pd.DataFrame(result.issues)
