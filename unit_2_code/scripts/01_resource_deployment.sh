# First, create a resource group (if you haven't already)
az group create `
--name aiagent-course-rg `
--location australiaeast

# Deploy the Bicep file
az deployment group create `
--resource-group aiagent-course-rg `
--template-file resource_deployment.bicep `
--parameters coursePrefix=courseunit431

# Get your deployment outputs
az deployment group show `
--resource-group aiagent-course-rg `
--name resource_deployment `
--query properties.outputs