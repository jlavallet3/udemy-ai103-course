# Make sure you have the Azure CLI installed and are logged in to your Azure account before running this script
az login

# First, create a resource group (if you haven't already)
az group create --name aiagent-course-rg --location eastus

# Convert the Bicep file to an ARM template (optional, for verification)
az bicep build --file 01_bicep_script_standard.bicep

# Deploy the 01 Bicep file
# az deployment group create `
#     --resource-group aiagent-course-rg `
#     --template-file 01_bicep_script_standard.bicep `
#     --parameters coursePrefix=unit1971course

# Deploy the 03 Bicep file
# az deployment group create `
#     --resource-group aiagent-course-rg `
#     --template-file 03_bicep_script_latest_model.bicep `
#     --parameters coursePrefix=unit1971course
    
# Deploy the 04 Bicep file
az deployment group create `
    --resource-group aiagent-course-rg `
    --template-file 04_bicep_script_improved.bicep `
    --parameters coursePrefix=unit1971course

# Get your 01 deployment outputs
# az deployment group show `
#     --resource-group aiagent-course-rg `
#     --name 01_bicep_script_standard `
#     --query properties.outputs

# Get your 03 deployment outputs
# az deployment group show `
#     --resource-group aiagent-course-rg `
#     --name 03_bicep_script_latest_model `
#     --query properties.outputs

# Get your 04 deployment outputs
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
    --name unit1971course;