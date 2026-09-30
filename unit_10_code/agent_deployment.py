import os
import sys
from pathlib import Path
from typing import Any, Dict
import yaml

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import CodeInterpreterTool, PromptAgentDefinition
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential

# =============================================================================
# CONFIGURATION
# =============================================================================

project_endpoint = os.getenv("PROJECT_ENDPOINT")
llm_model_deployment_name = os.getenv("LLM_MODEL_DEPLOYMENT_NAME")
script_path = Path(__file__).parent / "functions.py"

config_path = Path("config.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# =============================================================================
# AGENT FUNCTIONS
# =============================================================================


def create_or_update_agent(
    project_client: AIProjectClient,
    config: dict,
    llm_model_deployment_name: str,
) -> object:
    agent_name = config.get("agent_name")
    system_prompt = config.get("system_prompt")

    print(f"🔄 Processing agent: {agent_name}")

    # Use the OpenAI client for file operations
    print(f" 📤 Uploading functions script to Azure AI Foundry...")
    with project_client.get_openai_client() as openai_client:
        with open(script_path, "rb") as f:
            uploaded_file = openai_client.files.create(file=f, purpose="assistants")

    # Attach CodeInterpreterTool with the uploaded file ID
    print(" 🔍 Initializing CodeInterpreterTool with script file ID...")
    code_interpreter = CodeInterpreterTool(container={"file_ids": [uploaded_file.id]})

    try:
        print(f"   ✨ Creating or updating agent: {agent_name}")
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=llm_model_deployment_name,
                instructions=system_prompt,
                tools=[code_interpreter],  # Cloud-managed Code Interpreter
            ),
        )
        print(f"   ✅ Agent created or updated successfully (ID: {agent.id})")
        return agent

    except HttpResponseError as e:
        print(f"   ❌ Azure REST API Error: {e.message}")
        raise
    except Exception as e:
        print(f"   ❌ Unexpected error: {str(e)}")
        raise


# =============================================================================
# MAIN SCRIPT
# =============================================================================


def main() -> int:
    print("🚀 Starting agent deployment to Azure AI Foundry")
    print("=" * 60)

    try:
        credential = DefaultAzureCredential()
        with AIProjectClient(
            endpoint=project_endpoint, credential=credential
        ) as project_client:

            print(f"Connected to Azure AI Foundry project at: {project_endpoint}")
            agent = create_or_update_agent(
                project_client=project_client,
                config=config,
                llm_model_deployment_name=llm_model_deployment_name,
            )

        print("\n✨ Agent deployment completed successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
