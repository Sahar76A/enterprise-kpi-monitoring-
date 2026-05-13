# enterprise-kpi-monitoring-
A production-style Enterprise KPI Monitoring Platform that detects abnormal behavior in operational business metrics, attributes root causes, and generates alerts for investigation.

The system simulates how analytics and platform teams monitor critical KPIs such as revenue, order volume, and payment failures.
Key Features
• Automated KPI monitoring pipeline • Multi-model anomaly detection (Z-Score, IQR, Isolation Forest) • Root cause attribution across business dimensions • Risk severity classification for incidents • Operational alert orchestration system • Power BI monitoring console for investigation

Why This Project Exists
Organizations monitor operational KPIs to quickly detect incidents that impact customers or revenue.

Examples of operational incidents include:

• payment system failures • infrastructure outages • unexpected demand spikes • fraud or transaction anomalies

This project simulates how a modern analytics platform automatically detects these incidents and alerts operators.
Monitoring Console
The Enterprise KPI Monitoring Console provides a centralized operational view of business health.

The dashboard includes three monitoring layers.

Executive KPI Monitoring
• revenue trends • order volume trends • anomaly indicators • total alert summaries

Operational Risk Monitoring
• incident severity distribution • alert frequency over time • anomaly distribution across KPIs.
System Architecture
Raw Transaction Data
        │
        ▼
Feature Engineering
        │
        ▼
Daily KPI Aggregation
        │
        ▼
Anomaly Detection Layer
(Z-Score | IQR | Isolation Forest)
        │
        ▼
Risk Classification
        │
        ▼
Root Cause Attribution
        │
        ▼
Alert Orchestration Layer
        │
        ▼
Enterprise KPI Monitoring Console
The architecture mirrors how real data teams build monitoring systems for operational analytics.
Platform Components
Data Processing Layer
Transforms transaction-level data into daily KPI metrics.

Monitored KPIs

• Revenue • Orders • Payment failure rate • Average order value

Warehouse: DuckDB
Anomaly Detection Layer
Multiple anomaly detection methods run in parallel.

Z-Score Detector
Detects statistical deviations from historical baseline behavior.

IQR Detector
Identifies distribution outliers using interquartile ranges.

Isolation Forest
Machine learning model used to detect rare patterns in KPI behavior.

Combining statistical and ML detectors improves reliability and reduces false positives.

Risk Classification
Detected anomalies are categorized into severity levels.

Risk levels

• LOW • MEDIUM • HIGH

This prioritizes investigation and reduces alert noise.

Root Cause Attribution
When anomalies occur, the system analyzes dimensional breakdowns to identify likely drivers.

Example dimensions analyzed

• customer state • product category • payment method • order segment

This helps analysts understand why a KPI shifted, not just that it changed.

Alert Orchestration Layer
The alert orchestration system converts anomaly signals into operational notifications.

Key functions

• severity filtering • detector confirmation validation • alert suppression to reduce noise • incident prioritization • Slack-style notification generation

Example Alert
🔴 HIGH ALERT — Revenue KPI Anomaly

Date: 2018-07-07
Observed Value: $11,023
Baseline: $33,631
Z-Score: -1.96

Root Cause Signals
• customer_state: SP
• product_category: relogios_presentes
This simulates how monitoring platforms notify analytics teams of operational incidents.

Technology Stack
Core Processing
• Python • DuckDB (analytical warehouse) • Pandas / NumPy (data processing)

Machine Learning & Statistics
• Scikit-learn (Isolation Forest) • SciPy (statistical detection)

Configuration & Utilities
• PyYAML • python-dateutil

Visualization
• Power BI Monitoring Console
Project Structure
enterprise-kpi-monitoring
│
├── data
│   ├── raw/olist                 # Kaggle dataset
│   └── warehouse.duckdb
│
├── sql
│   ├── 00_create_staging.sql
│   └── 10_kpi_daily.sql
│
├── src
│   ├── config.py
│   ├── io_duckdb.py
│   ├── data_validation.py
│   ├── kpi_builder.py
│   ├── anomaly_injection.py
│   ├── baseline_engine.py
│   ├── anomaly_engine.py
│   ├── risk_engine.py
│   ├── root_cause_engine.py
│   ├── alert_orchestrator.py
│   ├── slack_formatter.py
│   └── pipeline.py
│
├── outputs
│   ├── kpi_daily.csv
│   ├── data_quality_report.csv
│   └── alerts.csv
│
├── run_pipeline.py
├── run_alerts.py
│
├── config.yaml
├── requirements.txt
└── README.md
How to Run the Project
Clone the repository

git clone https://github.com/yourusername/enterprise-kpi-monitoring
Install dependencies

pip install -r requirements.txt
Run the KPI pipeline

python run_pipeline.py
Generate anomaly alerts

python run_alerts.py
Load the Power BI dashboard using:

outputs/kpi_daily.csv
outputs/alerts.csv
Example Alert Output
The alert orchestration system generates operational notifications in:

outputs/slack_notifications.csv
These alerts simulate how monitoring systems notify analysts of KPI anomalies.

Skills Demonstrated
Data pipeline architecture Statistical anomaly detection Machine learning anomaly models Root cause attribution analysis Monitoring dashboard design Operational alert orchestration Analytics system architecture

Future Improvements
Real-time streaming ingestion Slack webhook integration Model drift monitoring Automated incident reports Streaming anomaly detection

What Makes This Project Valuable
This platform integrates anomaly detection, root cause analysis, monitoring dashboards, and alert orchestration to simulate a production KPI monitoring workflow.

It demonstrates how analytics systems evolve beyond dashboards into operational monitoring platforms used to track business health in real time.

Anomaly Investigation Console
• incident log • anomaly severity gauge • root cause signals • KPI anomaly breakdown
