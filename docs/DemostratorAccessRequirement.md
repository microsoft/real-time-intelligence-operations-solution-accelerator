# Demonstrator's Access Requirements  

If you deployed the solution accelerator via AZD following the [Deployment Guide](./DeploymentGuide.md), you have already established the required access to the solution, and **you can skip this Access Requirements section**, and start at [Step 1. Refresh Historical Data](#step-1-refresh-historical-data).

If you are using a demonstration environment already set up by someone else, you will need below accesses: 

1. You will need to be added as a contributor of the Fabric workspace. If you are a viewer, you will not be able to update any resources such as [Real-Time Intelligence Operations Dashboard](./RealTimeIntelligenceDashboardGuide.md) or [Activator](./ActivatorGuide.md). Recommend role: **contributor**. 
2. You will need to change the rules in Activator with your own outlook email that you have access to. 
3. You will need to be able to send simulated events to the Azure Event Hub deployed with the solution. The owner of the Event Hub or your Azure Admin can add you to the role of **Azure Event Hubs Data Sender**. Below diagram illustrates the key steps. 

![Event Hubs Data Sender Role](../docs/images/deployment/eventhubs-data-sender-role.png)
