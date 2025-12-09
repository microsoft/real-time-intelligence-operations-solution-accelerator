# Demonstrator's Guide

This guide provides instructions for demonstrating the Real-Time Intelligence Operations solution. Follow the steps in order to effectively showcase the system's capabilities.

## Access Prerequisites

Before beginning the demonstration, verify your access permissions:

- **If deployed using AZD:** You have the required access and may proceed directly to the demonstration steps.
- **If using a pre-configured environment:** Review the [Demonstrator Access Requirements](./DemonstratorAccessRequirement.md) guide to verify your access level.

---

## Step 1. Demonstrate the Fabric Data Agent

The Fabric Data Agent is an AI-powered assistant that provides natural language responses to business questions about your data.

**Instructions:**

1. Refer to the [Fabric Data Agent Guide](./FabricDataAgentGuide.md) for detailed setup instructions
2. After deployment (or if already deployed), locate the Data Agent in your Fabric workspace
3. Submit questions about the data using the [provided sample questions](./fabric_data_agent/user_sample_test_questions.md) or your own queries
4. Observe how the agent delivers instant responses in natural language

**What you'll see:**

![Fabric Data Agent UI](../docs/images/deployment/fabric_data_agent_ui.png)

## Step 2. Refresh Historical Data

The system contains 90 days of sample data. To ensure the demonstration reflects current information, you must refresh the dataset.

**Instructions:**

1. Follow the [Fabric Data Ingestion Guide](./FabricDataIngestion.md) for detailed procedures
2. Use the `--refresh-dates` and `--overwrite` options to update the data

This process takes approximately a few minutes and ensures the demonstration displays current data.

---

## Step 3. Initialize the Event Simulator

The Event Simulator generates realistic business events to demonstrate the system's real-time anomaly detection capabilities.

**Instructions:**

1. Refer to the [Event Simulator Guide](./EventSimulatorGuide.md) for detailed setup procedures
2. Start the simulator in **Normal Mode** to demonstrate standard operational conditions
3. Switch to **Anomaly Mode** to illustrate system detection and alert capabilities

You may switch operating modes or restart the simulator at any time during the demonstration without interrupting the session.

---

## Step 4. Present the Real-Time Intelligence Dashboard

The Real-Time Intelligence Operations Dashboard displays critical business metrics and provides real-time visibility into operational anomalies.

**Instructions:**

1. Refer to the [Dashboard Guide](./RealTimeIntelligenceDashboardGuide.md) for detailed information
2. On Fabric workspace Real-Time Dashboard, identify **anomaly spikes** in the data visualization. These represent potential operational issues
3. Configure the time filter to display "Last 24 Hours" or "Last 2 Days" corresponding to the simulator start time
4. Highlight the dashboard's real-time update capability as events are processed

**Example of anomaly spikes on the dashboard:**

![RTI Dashboard Anomaly Spikes](../docs/images/deployment/rti-dashboard-anomaly-spikes.png)

---

## Step 5. Demonstrate Alert Mechanisms with Activator

The Activator component monitors real-time data streams and automatically triggers alerts when anomalies exceed defined thresholds, enabling proactive incident response.

When anomalies are detected, the system automatically generates alerts, enabling teams to respond promptly to operational issues.

**Instructions:**

1. Review the [Activator Guide](./ActivatorGuide.md) to understand alert configuration and functionality
2. Open Activator from the workspace
3. Ensure alerts are configured to send to an accessible email address (configuration updates may be required)
4. Optionally configure alerts to be sent to a Microsoft Teams channel for team visibility

**Alert Behavior:**

- **Normal Mode:** Minimal anomalies result in infrequent alerts
- **Anomaly Mode:** Frequent anomalies trigger regular alert notifications

Example email notification:

![Anomaly Alert](../docs/images/deployment/anomaly-email-alerts.png)

When you open the email, it shows details like this:

![Activator Email Alert](../docs/images/deployment/activator-email-alert.png)

---

## Summary

You have successfully demonstrated the following capabilities:

1. **Intelligent Data Assistant:** Natural language query interface for business intelligence
2. **Real-Time Dashboard:** Comprehensive visualization of key operational metrics
3. **Automated Alerting:** Proactive notification system for anomaly detection
4. **Operational Response:** Integrated system enabling rapid response to critical events

These components work in concert to provide organizations with real-time operational visibility and accelerated incident response capabilities.
