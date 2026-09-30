import os
import sys
import yaml
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool
from azure.core.exceptions import HttpResponseError

# =============================================================================
# CONFIGURATION
# =============================================================================

project_endpoint = os.getenv("PROJECT_ENDPOINT")
llm_model_deployment_name = os.getenv("LLM_MODEL_DEPLOYMENT_NAME")
mcp_server_endpoint_1 = os.getenv("MCP_SERVER_ENDPOINT_1")
mcp_server_endpoint_2 = os.getenv("MCP_SERVER_ENDPOINT_2")
mcp_server_endpoint_3 = os.getenv("MCP_SERVER_ENDPOINT_3")

config_path = Path("config.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# =============================================================================
# AGENT FUNCTIONS
# =============================================================================


def create_or_update_agent(
    project_client: AIProjectClient, config: dict, llm_model_deployment_name: str
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

    # Configure the first mcp_tool with the provided server endpoint
    mcp_tools = []
    if len(mcp_server_endpoint_1) > 0:
        mcp_tool_1 = MCPTool(
            # let the name be the server_endpoint cleaned up to be a valid label
            server_label=mcp_server_endpoint_1.replace("https://", "")
            .replace("/", "-")
            .replace(".", "")
            .replace("-", "")
            .replace("mcp", ""),
            server_url=mcp_server_endpoint_1,
            require_approval="never",
        )
        mcp_tools.append(mcp_tool_1)
    if len(mcp_server_endpoint_2) > 0:
        mcp_tool_2 = MCPTool(
            server_label=mcp_server_endpoint_2.replace("https://", "")
            .replace("/", "-")
            .replace(".", "")
            .replace("-", "")
            .replace("mcp", ""),
            server_url=mcp_server_endpoint_2,
            require_approval="never",
        )
        mcp_tools.append(mcp_tool_2)
    if len(mcp_server_endpoint_3) > 0:
        mcp_tool_3 = MCPTool(
            server_label=mcp_server_endpoint_3.replace("https://", "")
            .replace("/", "-")
            .replace(".", "")
            .replace("-", "")
            .replace("mcp", ""),
            server_url=mcp_server_endpoint_3,
            require_approval="never",
        )
        mcp_tools.append(mcp_tool_3)

    try:
        print(f"   ✨ Creating or updating agent: {agent_name}")
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=llm_model_deployment_name,
                instructions=system_prompt,
                tools=mcp_tools,  # Attached the MCP Tools here
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

            print(f"Connected to Azure AI Foundry project at: {project_endpoint}")
            agent = create_or_update_agent(
                project_client, config, llm_model_deployment_name
            )

        print("\n✨ Agent deployment completed successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
