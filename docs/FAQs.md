# Frequently Asked Questions (FAQs)

#### **1. Question**: I need to test and adjust this solution accelerator to work with my own company's data. What approach should I take?

**Answer**: We recommend deploying and configuring this solution first to understand how the sample data is created, how information flows through the solution to the real-time intelligence operations dashboard, and how anomaly event notifications are sent to the specified Outlook email. Then you can customize the event simulator to generate your own data and develop your business cases for the real-time dashboard and email notifications. You can easily update the deployed Activator to send Teams notifications instead of Outlook emails.

#### **2. Question**: How was the real-time intelligence dashboard developed, and how can I customize it?

**Answer**: It was developed by creating a set of KQL query sets, testing the code, and reviewing the results. Then various dashboard tiles were developed, tested, and finalized. You can review the code in the folder `src/kql/real_time_dashboard/`. To customize the dashboard:

1. **Modify KQL queries**: Update the queries in the folder `src/kql/real_time_dashboard/` folder to match your data structure and business requirements
2. **Add new tiles**: Create additional KQL queries for new metrics or visualizations you need
3. **Update data sources**: Ensure your data schema matches the expected format, or modify the queries accordingly
4. **Test iteratively**: Deploy changes incrementally and test each modification

#### **3. Question**: What are the key components I need to understand in this solution?

**Answer**: The solution consists of several key components:

- **Event Simulator**: Generates synthetic manufacturing data for testing
- **Azure Event Hub**: Ingests real-time streaming data
- **Microsoft Fabric EventStream**: Processes and routes the streaming data
- **EventHouse/KQL Database**: Stores both historical and real-time data
- **Real-Time Dashboard**: Visualizes key metrics and trends
- **Fabric Activator**: Monitors for anomalies and sends notifications
- **Fabric Data Agent**: Provides AI-powered chat interface for data insights

#### **4. Question**: How do I configure anomaly detection thresholds?

**Answer**: Anomaly detection thresholds can be configured using data-driven approaches:

1. **Statistical Analysis**: Use the provided KQL queries in `src/kql/data_analysis/` to analyze your historical data and determine optimal thresholds using z-score or percentile methods
2. **Activator Configuration**: Update the Activator rules with the calculated thresholds
3. **Continuous Monitoring**: Regularly review and adjust thresholds based on operational experience and false positive rates

Refer to the [Data Analysis Guide](../src/kql/data_analysis/data_analysis_guide.md) for detailed threshold calculation methods.

#### **5. Question**: Can I integrate this solution with my existing systems?

**Answer**: Yes, this solution is designed to be extensible and can integrate with existing systems in several ways:

- **Data Integration**: Replace the event simulator with connectors to your actual manufacturing systems, IoT devices, or databases
- **Notification Systems**: Configure Activator to send alerts to your existing Teams channels, email systems, or ticketing platforms
- **API Integration**: Use Fabric's REST APIs to integrate with external monitoring or analytics platforms
- **Custom Applications**: Develop custom applications using the EventHouse data via KQL queries

#### **6. Question**: How do I troubleshoot common issues?

**Answer**: Common troubleshooting steps include:

1. **Data Flow Issues**: Check Event Hub metrics, EventStream status, and data ingestion logs
2. **Dashboard Not Updating**: Verify KQL queries, data connections, and refresh settings
3. **Missing Notifications**: Check Activator rule configuration, email settings, and threshold values
4. **Performance Issues**: Review KQL query efficiency and consider data partitioning strategies

For details on how the architecture components work together, refer to the [Technical Architecture Guide](./TechnicalArchitecture.md). 
