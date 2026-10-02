//https://github.com/microsoft-foundry/foundry-samples/blob/main/infrastructure/infrastructure-setup-bicep/00-basic/main.bicep

// -----------------------------
// General / naming
// -----------------------------
param coursePrefix string = 'mycourse' // short prefix used for tagging and defaults
param aiFoundryName string = coursePrefix // Cognitive Services account name / subdomain
param aiProjectName string = '${aiFoundryName}-proj' // Project name inside the account
param location string = resourceGroup().location

// -----------------------------
// API version
// -----------------------------
// Note: Bicep requires a literal API version in resource type tokens.
// Keep the literal below when updating resource versions.

// -----------------------------
// Account (AI Foundry / Cognitive Services)
// -----------------------------
param accountSkuName string = 'S0' // SKU name for the account (e.g., S0)
param accountSkuCapacity int = 1 // SKU capacity
param disableLocalAuth bool = false // whether local auth is disabled on the account

// -----------------------------
// Model deployment
// -----------------------------
param modelName string = 'gpt-5-mini' // deployed model resource name
param modelFormat string = 'OpenAI' // model format
param modelVersion string = '2025-08-07' // model version
param modelSkuName string = 'GlobalStandard' // deployment SKU name
param modelSkuCapacity int = 1 // deployment capacity

// -----------------------------
// Tags and metadata
// -----------------------------
param resourceTags object = {
  environment: 'dev'
  course: coursePrefix
}

/*
  An AI Foundry resources is a variant of a CognitiveServices/account resource type
*/ 
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2026-05-01' = {
  name: aiFoundryName
  location: location
  tags: resourceTags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: accountSkuName
    capacity: accountSkuCapacity
  }
  kind: 'AIServices'
  properties: {
    // required to work in AI Foundry
    allowProjectManagement: true

    // Defines developer API endpoint subdomain
    customSubDomainName: aiFoundryName

    disableLocalAuth: disableLocalAuth
  }
}

/*
  Developer APIs are exposed via a project, which groups in- and outputs that relate to one use case, including files.
  Its advisable to create one project right away, so development teams can directly get started.
  Projects may be granted individual RBAC permissions and identities on top of what account provides.
*/ 
resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2026-05-01' = {
  name: aiProjectName
  parent: aiFoundry
  location: location
  tags: resourceTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

/*
  Optionally deploy a model to use in playground, agents and other tools.
*/
resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2026-05-01' = {
  parent: aiFoundry
  name: modelName
  sku : {
    capacity: modelSkuCapacity
    name: modelSkuName
  }
  properties: {
    model:{
      name: modelName
      format: modelFormat
      version: modelVersion
    }
  }
}

output OPENAI_ENDPOINT string = 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/openai/v1'
output OPENAI_DEPLOYMENT_NAME string = modelDeployment.name
output AI_FOUNDY_NAME string = aiFoundry.name
output AI_PROJECT_NAME string = aiProject.name
output RESOURCE_TAGS object = resourceTags
