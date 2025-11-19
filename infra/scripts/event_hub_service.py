import json

try:
    from azure.eventhub import EventHubProducerClient, EventData
    from azure.eventhub.exceptions import EventHubError
    from azure.identity import DefaultAzureCredential
except ImportError:
    print("❌ Error: azure-eventhub and azure-identity packages are required.")
    print("Install them using: pip install azure-eventhub azure-identity")
    raise

class EventHubService:
    def __init__(self, fully_qualified_namespace: str, event_hub_name: str):
        self.fully_qualified_namespace = fully_qualified_namespace
        self.event_hub_name = event_hub_name
        self.credential = DefaultAzureCredential()

    def send_event(self, data: object):
        producer = EventHubProducerClient(
            fully_qualified_namespace=self.fully_qualified_namespace,
            eventhub_name=self.event_hub_name,
            credential=self.credential
        )

        event_json = json.dumps(data)
    
        with producer:
            event = EventData(event_json)
            
            event.properties = {
                "content-type": "application/json",
                "source": "EventHubService"
            }
            
            producer.send_event(event)
