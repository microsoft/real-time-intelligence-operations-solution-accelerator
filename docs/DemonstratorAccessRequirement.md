# Demonstrator's Access Requirements

To effectively demonstrate the Real-Time Intelligence Operations solution using a pre-configured environment, you must have the following permissions and access levels.

## 1. Fabric Workspace Contributor Role

You must have atleast **contributor** level access to the Fabric workspace to modify resources, including:

- [Real-Time Intelligence Operations Dashboard](./RealTimeIntelligenceDashboardGuide.md)
- [Activator](./ActivatorGuide.md)

> **Note:** Viewer-level access is insufficient for demonstration purposes.

## 2. Configure Activator Rules

Update the Activator rules with your Outlook email address to receive alert notifications.

### Steps to Update Activator Rule Email Address

1. Open the [Activator](./ActivatorGuide.md) in your Fabric workspace
2. Navigate to the rule you wish to modify
3. Locate the email notification settings on the right panel **Definations**
4. Replace the existing email address with your Outlook email address
5. Click **Save** to apply the changes
6. Verify you have access to the updated email account to receive alerts

## 3. Azure Event Hubs Data Sender Role

To send simulated events to the Azure Event Hub, you must have the **Azure Event Hubs Data Sender** role assigned to your account. Contact either the Event Hub owner, or your Azure Administrator to request this role assignment.

The diagram below illustrates the role assignment process:

![Event Hubs Data Sender Role](../docs/images/deployment/eventhubs-data-sender-role.png)
