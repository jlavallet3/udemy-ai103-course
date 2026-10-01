import os
import sys
import yaml
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    MemorySearchPreviewTool,
    MemoryStoreDefaultDefinition,
)
from azure.core.exceptions import HttpResponseError

# =============================================================================
# CONFIGURATION
# =============================================================================

project_endpoint = os.getenv("PROJECT_ENDPOINT")
llm_model_deployment_name = os.getenv("LLM_MODEL_DEPLOYMENT_NAME")
embedding_model_deployment_name = os.getenv("EMBEDDING_MODEL_DEPLOYMENT_NAME")

config_path = Path("config.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# =============================================================================
# AGENT FUNCTIONS
# =============================================================================


def get_or_create_memory_store(project_client: AIProjectClient, store_name: str) -> str:
    """
    Provision or retrieve a managed Memory Store in Azure AI Foundry.
    """
    print(f"🧠 Checking Memory Store: {store_name}")

    try:
        # 1. Try retrieving the existing memory store
        memory_store = project_client.beta.memory_stores.get(store_name)
        print(f"   ℹ️ Found existing Memory Store: {memory_store.name}")
        return memory_store.name

    except HttpResponseError as e:
        # 2. If it doesn't exist (404/ResourceNotFound), create it
        if "NotFound" in str(e) or e.status_code == 404:
            print(f"   ✨ Creating new Memory Store: {store_name}")
            memory_definition = MemoryStoreDefaultDefinition(
                chat_model=llm_model_deployment_name,
                embedding_model=embedding_model_deployment_name,
            )
            memory_store = project_client.beta.memory_stores.create(
                name=store_name,
                definition=memory_definition,
                description="Agent long-term user preference memory store",
            )
            print(f"   ✅ Memory Store created: {memory_store.name}")
            return memory_store.name
        else:
            # Re-raise if it's an unexpected API error
            raise


def create_or_update_agent(
    project_client: AIProjectClient,
    config: dict,
    llm_model_deployment_name: str,
    memory_store_name: str,
) -> object:
    """
    Create or update a server-side agent in the Azure AI Foundry project.

    Args:
        project_client: Authenticated AIProjectClient instance
        config: Agent configuration dictionary from YAML

    Returns:
        The created or updated Agent object
    """
    agent_name = config.get("agent_name")
    system_prompt = config.get("system_prompt")

    print(f"🔄 Processing agent: {agent_name}")

    try:
        # Define memory tool attached to the memory store
        memory_tool = MemorySearchPreviewTool(
            memory_store_name=memory_store_name,
            scope="{{$userId}}",  # Scopes memories dynamically per user
        )

        print(f"   ✨ Creating or updating agent: {agent_name}")
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=llm_model_deployment_name,
                instructions=system_prompt,
                tools=[memory_tool],
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
        # Initialize client via context manager
        credential = DefaultAzureCredential()
        with AIProjectClient(
            endpoint=project_endpoint, credential=credential
        ) as project_client:

            # Step 1: Ensure Memory Store exists
            memory_store_name = get_or_create_memory_store(
                project_client,
                store_name=f"{config.get('agent_name', 'foundry')}-memory-store",
            )

            print(f"Connected to Azure AI Foundry project at: {project_endpoint}")
            # Step 2: Create or update agent with memory tool configured
            agent = create_or_update_agent(
                project_client, config, llm_model_deployment_name, memory_store_name
            )

        print("\n✨ Agent deployment completed successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
