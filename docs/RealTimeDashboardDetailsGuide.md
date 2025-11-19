# Real-Time Intelligence Operations Dashboard Guide

## Overview

The Real-Time Intelligence Dashboard provides instant visibility into the health and performance of key assets at manufacturing facility located at **Contoso Outdoors – Ho Chi Minh Facility**.
It monitors two critical assets:

- **Robotic Arm 1 (A_1000)**
- **Packaging Line 1 (A_1001)**

The dashboard uses **live sensor data, Z-score–based anomaly detection**, and **trend analysis** to help teams identify issues early, prevent downtime, and improve product quality. For more information about the statistical z-score analysis, please refer to [Data Analysis Guide](../src/kql/data_analysis/data_analysis_guide.md) for the details. 

## Data Requirement 

The dashboard is dependent on the quality of the underling data set. To get a good dashboard analysis based on sample data provided by this solution accelerator, please refresh the historical data by following   [Fabric Data Ingestion Guide](./FabricDataIngestion.md) and then start real time simulator by following the [Event Simulator Guide](./EventSimulatorGuide.md). The event simulator simulates the real time telemetry data streaming into the Fabric Event House, which the data source of the RTI Operations Dashboard. It has different modes of operations. It can provide normal telemetry or enhanced anomaly mode. 

## RTI Dashboard 

---

There are two pages of ... (Yamini)

Displays the latest sensor readings for each asset with real-time anomaly status. Each row represents one asset, showing current values for **Speed**, **Temperature**, **Vibration**, and **Defect Probability** alongside their health status indicators. Each reading is evaluated using Z-score thresholds and color-coded for quick understanding (see Key Concepts section above).

**Business Value:**

- **Immediate Alerts:** Know which equipment needs attention RIGHT NOW
- **Statistical Context:** Z-scores show how abnormal current readings are compared to historical baseline
- **Prioritization:** Color coding helps focus on critical issues first
- **Comprehensive View:** See all key metrics for each asset in one place

#### Page 1: Asset Performance Overview

This page serves as main monitoring view. It shows current equipment health, sensor status, and key performance trends.



![image](images/readme/rti-dashboard-pg1.png)

##### Tile 1: Real Time Sensor Status with Z-Score Analysis

Yamini to make the content condense. ... 

- 

---

### Asset Quality Metrics

Side-by-side comparison of anomaly rates and quality issues between assets in a column chart format. Uses Z-score analysis with a 30-day baseline (see Key Concepts for thresholds).

**Key Metrics Displayed:**
- **Anomaly Rate %:** Combined percentage of speed, temperature, and vibration anomalies
- **Quality Issues %:** Percentage of events with defect probability exceeding 5%



---

### Trend Analysis 
These tiles named Speed Trend, Temperature Trend, or Vibration Trend  displays each sensor data respectively. Defect Probability is the predicted Defect Probability based on the values of the other three sensor data. 

---

## Page 2: Advanced Analytics & Anomaly Insights

This page provides deeper insights into operational patterns, correlations, and maintenance status for advanced troubleshooting and strategic planning.

(images/readme/rti-dashboard-pg2.png)



---

### Tile 2: Anomaly Correlation Matrix
This table highlights how often different sensor metrics experience anomalies together. In other words, it answers:

- *When Speed shows an anomaly, how likely is Temperature also abnormal?*
- *Do vibration issues often occur alongside quality problems?*

**Columns Explained:**

- **Asset**: Name of the equipment being monitored.
- **Speed→Temp**: How often speed anomalies coincide with temperature anomalies.
- **Speed→Vibration**: Indicates if speed fluctuations are linked to mechanical stress.
- **Speed→Quality**: Shows whether abnormal speed impacts defect probability.
- **Temp→Vibration**: Correlation between thermal issues and vibration problems.
- **Temp→Quality**: Highlights if overheating affects product quality.
- **Vibration→Quality**: Relationship between mechanical health and manufacturing precision.
- **Total Anomalies**: Combined count of all anomaly events for the asset.

**Example Interpretations:**

- High Speed→Vibration = Speed variations causing mechanical stress
- High Temp→Quality = Overheating directly impacting product quality
- High Vibration→Quality = Mechanical issues affecting manufacturing precision

**Business Value:**
- **Root Cause Analysis:** Understand cascading failures and shared causes
- **Predictive Insights:** If metric A fails, expect metric B to follow
- **Maintenance Strategy:** Fix underlying causes, not just symptoms
- **Troubleshooting:** Guide technicians to probable root causes
