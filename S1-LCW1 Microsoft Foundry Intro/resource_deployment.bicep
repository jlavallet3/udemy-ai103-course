//https://github.com/microsoft-foundry/foundry-samples/blob/main/infrastructure/infrastructure-setup-bicep/00-basic/main.bicep

param coursePrefix string
param aiFoundryName string = coursePrefix
param aiProjectName string = '${aiFoundryName}-proj'
param llmModelDeploymentName string = '${coursePrefix}-llm-deploy'
param location string = resourceGroup().location

/*
  An AI Foundry resources is a variant of a CognitiveServices/account resource type that is specifically designed
   to host AI workloads and provide a seamless experience for deploying and managing AI models and assets.
*/ 
resource aiFoundry 'Microsoft.CognitiveServices/accounts@2026-05-01' = {
  name: aiFoundryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    // required to work in AI Foundry
    allowProjectManagement: true

    // Defines developer API endpoint subdomain
    customSubDomainName: aiFoundryName

    disableLocalAuth: false
  }
}

/*
  An AI Project is a logical container for assets such as models, deployments, etc. within the AI Foundry. 
  It is required to create an AI Project before deploying any models or other assets.
*/
resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2026-05-01' = {
  name: aiProjectName
  parent: aiFoundry
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

/*
  Deploying a model to the AI Foundry is done through a deployment resource.
  In this example, we are deploying the 'gpt-5-mini' model, 
  which is a variant of GPT-5 optimized for lower latency and 
  cost while still providing strong performance for many use cases.
*/
resource llmModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2026-05-01'= {
  parent: aiFoundry
  name: llmModelDeploymentName
  sku : {
    capacity: 50 // The rate limit for the deployment, in requests per minute. Adjust based on your expected usage.
    name: 'GlobalStandard'
  }
  properties: {
    model:{
      name: 'gpt-5-mini'
      format: 'OpenAI'
      version: '2025-08-07'
    }
  }
}

/*
  OUTPUTS
*/
output openai_endpoint string = 'https://${aiFoundry.properties.customSubDomainName}.services.ai.azure.com/openai/v1'
output llm_model_deployment_name string = llmModelDeployment.name
