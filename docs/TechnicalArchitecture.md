# Solution Architecture Description

The solution architecture is illustrated below. During deployment, 90 days of events were generated and stored in the Fabric EventHouse database. After the deployment, the `Telemetry Data Simulator` can be invoked at any time to generate real-time events. Please refer to [Event Simulator Guide](./EventSimulatorGuide.md) for details on the usage. The real-time data is ingested into Event Hub which sends to Fabric EventStream. The EventStream ingests data into EventHouse. The `events` table in the EventHouse database hosts combined historical data and real-time data, which is used by the real-time intelligence dashboard via Kusto Query Language (KQL) queries. The EventStream data is also fed into the Activator. The Activator has built-in intelligence to detect anomalies and send notifications via specified email notifications. 

Since the 90 days of historical data were generated during the deployment and will become stale after some time, to solve this problem, we have provided a utility called `Fabric Data Ingester` (not shown in the diagram) which refreshes the events data, replacing old data with fresh 90-day data. Please refer to [Fabric Data Ingestion Guide](./FabricDataIngester.md) for details on the usage. 

In summary, we built a working solution with data simulators to provide a live environment where you can observe or demo the capabilities. 

![Architecture](./images/readme/solution-architecture.png)



