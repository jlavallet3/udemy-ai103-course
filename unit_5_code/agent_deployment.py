import os
import sys
import yaml
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    FileSearchTool,
)
from azure.core.exceptions import HttpResponseError

# =============================================================================
# CONFIGURATION
# =============================================================================

project_endpoint = os.getenv("PROJECT_ENDPOINT")
llm_model_deployment_name = os.getenv("LLM_MODEL_DEPLOYMENT_NAME")
file_to_upload = os.getenv("FILE_TO_UPLOAD")

config_path = Path("config.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# =============================================================================
# VECTOR STORE FUNCTIONS
# =============================================================================


def upload_and_build_vector_store(
    project_client: AIProjectClient, pdf_path: str
) -> object:
    """Uploads a document to Azure AI Foundry and attaches it to a new Vector Store.

    Args:
        project_client: Authenticated AIProjectClient instance.
        pdf_path: Local file path to the PDF document.

    Returns:
        The created VectorStore object containing the indexed file.
    """
    path_obj = Path(pdf_path).resolve()
    print(f"📄 Processing document: {path_obj.name}")

    openai_client = project_client.get_openai_client()

    # 1. Upload file with explicit filename tuple to preserve MIME type & metadata
    print(f"⚡ Uploading raw document ({path_obj.stat().st_size / 1024:.2f} KB)...")
    with open(path_obj, "rb") as file_stream:
        uploaded_file = openai_client.files.create(
            file=(path_obj.name, file_stream), purpose="assistants"
        )
    print(
        f"   ✅ File uploaded (File ID: {uploaded_file.id}, Bytes: {uploaded_file.bytes})"
    )

    # 2. Create a uniquely named Vector Store
    print("⚡ Creating Vector Store for Knowledge Base...")
    vector_store_name = f"knowledge_base_{os.urandom(4).hex()}"
    vector_store = openai_client.vector_stores.create(name=vector_store_name)
    print(
        f"   ✅ Vector Store created (Vector Store ID: {vector_store.id}, Name: {vector_store_name})"
    )

    # 3. Attach file ID and poll until indexing/chunking finishes
    print("⚡ Indexing document into Vector Store (polling status)...")
    file_batch = openai_client.vector_stores.file_batches.create_and_poll(
        vector_store_id=vector_store.id, file_ids=[uploaded_file.id]
    )
    print(f"   ✅ File successfully indexed! (Status: {file_batch.status})")

    return vector_store


# =============================================================================
# AGENT FUNCTIONS
# =============================================================================


def create_or_update_agent(
    project_client: AIProjectClient,
    config: dict,
    llm_model_deployment_name: str,
    vector_store_id: str,
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
        # Initialize the File Search Tool configured with our Vector Store
        file_search_tool = FileSearchTool(vector_store_ids=[vector_store_id])

        print(f"   ✨ Creating or updating agent: {agent_name}")
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=llm_model_deployment_name,
                instructions=system_prompt,
                tools=[file_search_tool],
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

            # Upload file & build vector store knowledge base
            vector_store = upload_and_build_vector_store(project_client, file_to_upload)

            print(f"Connected to Azure AI Foundry project at: {project_endpoint}")
            agent = create_or_update_agent(
                project_client,
                config,
                llm_model_deployment_name,
                vector_store_id=vector_store.id,
            )

        print("\n✨ Agent deployment completed successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
