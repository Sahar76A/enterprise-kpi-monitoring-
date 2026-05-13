from pathlib import Path
from src.alert_orchestrator import orchestrate_alerts


if __name__ == "__main__":
    result = orchestrate_alerts(
        alerts_path=Path("outputs/alerts.csv"),
        output_path=Path("outputs/slack_notifications.csv"),
        cooldown_days=3,
    )

    print("\n=== ALERT ORCHESTRATION RESULT ===")
    print(f"status: {result.status}")
    print(f"input_alerts: {result.input_alerts}")
    print(f"meaningful_alerts: {result.meaningful_alerts}")
    print(f"notifications_generated: {result.notifications_generated}")
    print(f"output_path: {result.output_path}")
