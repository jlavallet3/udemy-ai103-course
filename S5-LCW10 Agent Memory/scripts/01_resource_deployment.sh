# First, create a resource group (if you haven't already)
az group create `
--name aiagent-course-rg `
--location eastus

# Deploy the Bicep file
az deployment group create `
--resource-group aiagent-course-rg `
--template-file resource_deployment.bicep `
--parameters coursePrefix=ccourseunit1977

# Get your deployment outputs
az deployment group show `
--resource-group aiagent-course-rg `
--name resource_deployment `
--query properties.outputs