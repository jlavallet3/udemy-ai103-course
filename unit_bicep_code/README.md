# Unit: Introduction to Bicep (AI Foundry)

This unit introduces Bicep for provisioning Azure resources used with AI Foundry. You'll learn how to read, customize, and deploy Bicep templates that create an AI Foundry account, project, and model deployment.

## What you'll learn

- Bicep basics: parameters, resources, outputs
- How the AI Foundry (Cognitive Services AIServices) resources are modeled in Bicep
- Deploying templates using the Azure CLI (`az`) and Bicep
- Differences between standard, debug, latest-model, and improved scripts
- Practical tips for parameterizing and organizing templates

## Prerequisites

- An Azure subscription with permission to create resources
- Azure CLI installed and signed in (`az login`)
- Bicep CLI (optional; `az deployment` can build Bicep automatically)

## Unit Plan

1. Show how to deploy Foundry via the Azure Portal
2. Walk through the template source and structure
3. Deploy the `01_bicep_script_standard.bicep` (includes `az login` demo)
4. Inspect `02_bicep_script_debug.bicep`
5. Deploy `03_bicep_script_latest_model.bicep` to show model updates
6. Explore `04_bicep_script_improved.bicep` — better parameterization and organization