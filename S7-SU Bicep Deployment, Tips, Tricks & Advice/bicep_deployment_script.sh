# Make sure you have the Azure CLI installed and are logged in to your Azure account before running this script
az login

# First, create a resource group (if you haven't already)
az group create --name aiagent-course-rg --location eastus

# Convert the Bicep file to an ARM template (optional, for verification)
az bicep build --file 04_bicep_script_improved.bicep

# Deploy the Bicep file
az deployment group create `
    --resource-group aiagent-course-rg `
    --template-file 04_bicep_script_improved.bicep `
    --parameters coursePrefix=unit1986course

# Get your deployment outputs
az deployment group show `
    --resource-group aiagent-course-rg `
    --name 04_bicep_script_improved `
    --query properties.outputs

# Delete the entire deployment (So no more costs)
az group delete `
    --name aiagent-course-rg `
    --yes

# Verify deletion of deployed resources
az group list --output table

# View recently deleted Cognitive Services accounts in the region (to confirm deletion)
az cognitiveservices account list-deleted --output table

# The following commands permanently delete the soft-deleted accounts.
az cognitiveservices account purge `
    --location eastus `
    --resource-group aiagent-course-rg `
    --name foundrycourse1;

az cognitiveservices account purge `
    --location eastus `
    --resource-group aiagent-course-rg `
    --name unit1986course;