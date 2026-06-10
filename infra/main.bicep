metadata name = 'Real-time Ingestion Fabric Solution Accelerator'
metadata description = '''SAS Gold Standard Solution Accelerator for Real-time Ingestion with Fabric.
'''

// ============================================================================
// PARAMETERS
// ============================================================================
@minLength(1)
@maxLength(20)
@description('Optional. A friendly string representing the application/solution name to give to all resource names in this deployment. This should be 3-16 characters long.')
param solutionName string = 'rtifsa'

@maxLength(5)
@description('Optional. A unique text value for the solution. This is used to ensure resource names are unique for global resources. Defaults to a 5-character substring of the unique string generated from the subscription ID, resource group name, and solution name.')
param solutionUniqueText string = substring(uniqueString(subscription().id, resourceGroup().name, solutionName), 0, 5)

@minLength(3)
@metadata({ azd: { type: 'location' } })
@description('Optional. Azure region for all services. Defaults to the tenant\' location to avoid usage of Microsoft Fabric multi-geo capabilities.')
param location string = resourceGroup().location

@description('Optional. Enable/Disable usage telemetry for module.')
param enableTelemetry bool = true

@description('Optional. An array of user object IDs or service principal object IDs that will be assigned the Fabric Capacity Admin role. This can be used to add additional admins beyond the default admin which is the user assigned managed identity created as part of this deployment.')
param fabricAdminMembers array = []

@allowed([
  'F2'
  'F4'
  'F8'
  'F16'
  'F32'
  'F64'
  'F128'
  'F256'
  'F512'
  'F1024'
  'F2048'
])
@description('Optional. SKU tier of the Fabric resource.')
param skuName string = 'F2'

@description('Specifies the object id of a Microsoft Entra ID user to allow Event Hub data access for event simulation. This is typically the object id of the system administrator who deploys the Azure resources. Defaults to the deploying user.')
param userObjectId string = deployer().objectId

@description('Optional. Tags to apply to all resources.')
param tags resourceInput<'Microsoft.Resources/resourceGroups@2025-04-01'>.tags = {}

// ============================================================================
// EXISTING RESOURCE PARAMETERS
// When provided, the deployment uses existing resources instead of creating new
// ones. These are expected to be set via `azd env set` before `azd up`.
// ============================================================================

@description('Optional. Resource ID of an existing Event Hub Namespace to use. When provided, a new Event Hub Namespace will not be created. A new Event Hub will always be created in either the existing or new namespace.')
param existingEventHubNamespaceId string = ''

@description('Optional. Name of an existing Fabric Capacity to use. When provided, a new Fabric Capacity will not be created.')
param existingFabricCapacityName string = ''

// ============================================================================
// VARIABLES
// ============================================================================

// ============================================================================
// Determine whether to use existing resources
// ============================================================================

// Use an existing namespace if a valid resource ID is provided; otherwise create a new one.
// A new Event Hub is always created to avoid mixing unrelated event types.
var useExistingEventHubNamespace = startsWith(existingEventHubNamespaceId, '/subscriptions/')
// Fallback placeholder ensures split() is always called on a well-formed resource ID.
var _safeEventHubNamespaceId = useExistingEventHubNamespace
  ? existingEventHubNamespaceId
  : '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/placeholder/providers/Microsoft.EventHub/namespaces/placeholder'
var eventHubNamespaceNameFromId = last(split(_safeEventHubNamespaceId, '/'))
var eventHubNamespaceSubscriptionId = split(_safeEventHubNamespaceId, '/')[2]
var eventHubNamespaceResourceGroup = split(_safeEventHubNamespaceId, '/')[4]
// Use an existing Fabric capacity if a valid name is provided; otherwise create a new one.
var useExistingFabricCapacity = !empty(existingFabricCapacityName) && !startsWith(existingFabricCapacityName, '$')

var solutionSuffix = toLower(trim(replace(
  replace(
    replace(replace(replace(replace('${solutionName}${solutionUniqueText}', '-', ''), '_', ''), '.', ''), '/', ''),
    ' ',
    ''
  ),
  '*',
  ''
)))

@description('Tag, Created by user name')
param createdBy string = contains(deployer(), 'userPrincipalName')
  ? split(deployer().userPrincipalName, '@')[0]
  : deployer().objectId

var allTags = union(
  {
    'azd-env-name': solutionName
    TemplateName: 'Real-time Ingestion Fabric Solution Accelerator'
    Type: 'Non-WAF'
    CreatedBy: createdBy
  },
  tags
)

var eventHubTags = union(allTags, {
  SecurityControl: 'Ignore' // Required to override MSFT subscription policy controls that enforce disableLocalAuth; local auth needed for Fabric SAS connection
})

resource resourceGroupTags 'Microsoft.Resources/tags@2023-07-01' = {
  name: 'default'
  properties: {
    tags: union(reference(resourceGroup().id, '2023-07-01', 'Full').?tags ?? {}, allTags)
  }
}

// ============================================================================
// EVENT HUB (Azure)
// ============================================================================

var eventHubNamespaceName = useExistingEventHubNamespace ? eventHubNamespaceNameFromId : 'evhns${solutionSuffix}'
// Always create a new Event Hub to avoid mixing unrelated event types (best practice)
var eventHubName = 'evh${solutionSuffix}'

// Deploy Event Hub to existing namespace (supports cross-subscription/cross-RG scenarios)
// The module is deployed to the namespace's actual location, which may be:
//   - Different resource group in same subscription
//   - Different subscription entirely
// Bicep requires a module for cross-scope deployments
module eventHubCrossScope 'modules/event-hub.bicep' = if (useExistingEventHubNamespace) {
  name: take('event-hub-${eventHubName}', 64)
  scope: resourceGroup(eventHubNamespaceSubscriptionId, eventHubNamespaceResourceGroup)
  params: {
    namespaceName: eventHubNamespaceNameFromId
    eventHubName: eventHubName
    userObjectId: userObjectId
    messageRetentionInDays: 1
  }
}

// Create a new Event Hub Namespace with an Event Hub when not using an existing namespace.
module eventHubNamespaceModule 'br/public:avm/res/event-hub/namespace:0.14.1' = if (!useExistingEventHubNamespace) {
  name: take('avm.res.event-hub.namespace.${eventHubNamespaceName}', 64)
  params: {
    name: eventHubNamespaceName
    location: location
    skuName: 'Standard'
    skuCapacity: 1
    disableLocalAuth: false // NOTE: local auth is currently needed in order to create connection with Fabric via SAS token
    tags: eventHubTags
    eventhubs: [
      {
        name: eventHubName
        messageRetentionInDays: 1
        roleAssignments: [
          {
            roleDefinitionIdOrName: 'Azure Event Hubs Data Sender'
            principalId: userObjectId
          }
        ]
      }
    ]
    enableTelemetry: enableTelemetry
  }
}

// ============================================================================
// FABRIC CAPACITY (Azure)
// ============================================================================

var fabricCapacityResourceName = useExistingFabricCapacity ? existingFabricCapacityName : 'fc${solutionSuffix}'
var fabricCapacityDefaultAdmins = deployer().?userPrincipalName == null
  ? [deployer().objectId]
  : [deployer().userPrincipalName]
var fabricTotalAdminMembers = union(fabricCapacityDefaultAdmins, fabricAdminMembers)

// Create new Fabric Capacity when not using existing resources
module fabricCapacity 'br/public:avm/res/fabric/capacity:0.1.2' = if (!useExistingFabricCapacity) {
  name: take('avm.res.fabric.capacity.${fabricCapacityResourceName}', 64)
  params: {
    name: fabricCapacityResourceName
    location: location
    skuName: skuName
    adminMembers: fabricTotalAdminMembers
    enableTelemetry: enableTelemetry
  }
}

// ============================================================================
// OUTPUTS
// ============================================================================

@description('The location the resources were deployed to')
output AZURE_LOCATION string = location

@description('The name of the resource group')
output AZURE_RESOURCE_GROUP string = resourceGroup().name

@description('The name of the Fabric capacity resource')
#disable-next-line BCP318
output AZURE_FABRIC_CAPACITY_NAME string = useExistingFabricCapacity
  ? existingFabricCapacityName
  : fabricCapacity!.outputs.name

@description('The identities added as Fabric Capacity Admin members')
output AZURE_FABRIC_CAPACITY_ADMINISTRATORS array = fabricTotalAdminMembers

@description('The resource ID of the Event Hub Namespace for ingestion.')
#disable-next-line BCP318
output AZURE_EVENT_HUB_NAMESPACE_ID string = useExistingEventHubNamespace
  ? existingEventHubNamespaceId
  : eventHubNamespaceModule!.outputs.resourceId

@description('The name of the Event Hub Namespace for ingestion.')
#disable-next-line BCP318
output AZURE_EVENT_HUB_NAMESPACE_NAME string = useExistingEventHubNamespace
  ? eventHubNamespaceNameFromId
  : eventHubNamespaceModule!.outputs.name

@description('The hostname of the Event Hub Namespace for ingestion.')
#disable-next-line BCP318
output AZURE_EVENT_HUB_NAMESPACE_HOSTNAME string = useExistingEventHubNamespace
  ? '${eventHubNamespaceNameFromId}.servicebus.windows.net'
  : '${eventHubNamespaceModule!.outputs.name}.servicebus.windows.net'

@description('The name of the Event Hub for ingestion.')
output AZURE_EVENT_HUB_NAME string = eventHubName

@description('The solution name suffix used for resource naming.')
output SOLUTION_SUFFIX string = solutionSuffix

@description('Indicates whether an existing Event Hub Namespace was used.')
output USING_EXISTING_EVENT_HUB_NAMESPACE bool = useExistingEventHubNamespace

@description('Indicates whether existing Fabric Capacity was used.')
output USING_EXISTING_FABRIC_CAPACITY bool = useExistingFabricCapacity

@description('The resource group name where the Event Hub Namespace is located. May differ from deployment RG when reusing namespace from different location.')
output AZURE_EVENT_HUB_RESOURCE_GROUP string = useExistingEventHubNamespace
  ? eventHubNamespaceResourceGroup
  : resourceGroup().name

@description('The subscription ID where the Event Hub Namespace is located. May differ from deployment subscription when reusing namespace from different subscription.')
output AZURE_EVENT_HUB_SUBSCRIPTION_ID string = useExistingEventHubNamespace
  ? eventHubNamespaceSubscriptionId
  : subscription().subscriptionId
