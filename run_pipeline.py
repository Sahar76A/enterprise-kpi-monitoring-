from src.config import load_config
from src.pipeline import run_pipeline

if __name__ == "__main__":
    conf = load_config("config.yaml")
    result = run_pipeline(conf)

    print("\n=== PIPELINE RESULT ===")
    for k, v in result.items():
        print(f"{k}: {v}")

    if result["status"] == "OK":
        print("\nNext: Import outputs/alerts.csv into Power BI and build the dashboard pages.")
    elif result["status"] == "STOPPED_DATA_QUALITY_FAIL":
        print("\nFix data quality failures first. See outputs/data_quality_report.csv.")
