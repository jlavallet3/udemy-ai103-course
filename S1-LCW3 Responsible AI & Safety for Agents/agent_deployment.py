import os
import sys
import yaml
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, RaiConfig
from azure.core.exceptions import HttpResponseError

from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
from azure.mgmt.cognitiveservices.models import (
    RaiPolicy,
    RaiPolicyProperties,
    RaiPolicyContentFilter,
    ContentLevel,
    RaiPolicyContentSource,
    RaiPolicyMode,
)

# =============================================================================
# CONFIGURATION
# =============================================================================

subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
resource_group_name = os.getenv("AZURE_RESOURCE_GROUP")
account_name = os.getenv("AZURE_COGNITIVE_ACCOUNT_NAME")

project_endpoint = os.getenv("PROJECT_ENDPOINT")
llm_model_deployment_name = os.getenv("LLM_MODEL_DEPLOYMENT_NAME")

config_path = Path("config.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# =============================================================================
# AGENT FUNCTIONS
# =============================================================================


def create_or_update_rai_policy(
    credential: DefaultAzureCredential,
    subscription_id: str,
    resource_group_name: str,
    account_name: str,
    config: dict,
) -> str:
    """Creates or updates a custom RAI Policy programmatically using the Azure Management SDK.

    Returns the full ARM Resource ID of the created policy.
    """

    policy_name = config["guardrails"]["rai_policy_name"]

    print(f"🛡️ Defining and deploying RAI Policy: '{policy_name}'...")

    mgmt_client = CognitiveServicesManagementClient(
        credential=credential, subscription_id=subscription_id
    )

    content_filters = []

    # Add Jailbreak Protection
    content_filters.append(
        RaiPolicyContentFilter(
            name="Jailbreak",
            source=RaiPolicyContentSource.PROMPT,
            blocking=config["guardrails"]["controls"]["jailbreak"]["action"] == "Block",
            enabled=config["guardrails"]["controls"]["jailbreak"]["enabled"],
        )
    )

    # Add Indirect Prompt Injection
    content_filters.append(
        RaiPolicyContentFilter(
            # name="Indirect Prompt Injection", # Not supported
            name="Indirect Attack",
            # name="Prompt Shield", # Not supported
            source=RaiPolicyContentSource.PROMPT,
            blocking=config["guardrails"]["controls"]["indirect_prompt_injections"][
                "action"
            ]
            == "Block",
            enabled=config["guardrails"]["controls"]["indirect_prompt_injections"][
                "enabled"
            ],
        ),
    )

    # Add Content Harms filters (Hate, Sexual, Self-Harm, Violence) based on the configuration
    content_filters.extend(
        [
            RaiPolicyContentFilter(
                name="Hate",
                source=RaiPolicyContentSource.PROMPT,
                severity_threshold={
                    "High": ContentLevel.LOW,
                    "Medium": ContentLevel.MEDIUM,
                    "Low": ContentLevel.HIGH,
                }.get(config["guardrails"]["controls"]["content_harms"]["hate"]),
                blocking=config["guardrails"]["controls"]["content_harms"]["action"]
                == "Block",
                enabled=config["guardrails"]["controls"]["content_harms"]["enabled"],
            ),
            RaiPolicyContentFilter(
                name="Hate",
                source=RaiPolicyContentSource.COMPLETION,
                severity_threshold={
                    "High": ContentLevel.LOW,
                    "Medium": ContentLevel.MEDIUM,
                    "Low": ContentLevel.HIGH,
                }.get(config["guardrails"]["controls"]["content_harms"]["hate"]),
                blocking=config["guardrails"]["controls"]["content_harms"]["action"]
                == "Block",
                enabled=config["guardrails"]["controls"]["content_harms"]["enabled"],
            ),
            RaiPolicyContentFilter(
                name="Sexual",
                source=RaiPolicyContentSource.PROMPT,
                severity_threshold={
                    "High": ContentLevel.LOW,
                    "Medium": ContentLevel.MEDIUM,
                    "Low": ContentLevel.HIGH,
                }.get(config["guardrails"]["controls"]["content_harms"]["sexual"]),
                blocking=config["guardrails"]["controls"]["content_harms"]["action"]
                == "Block",
                enabled=config["guardrails"]["controls"]["content_harms"]["enabled"],
            ),
            RaiPolicyContentFilter(
                name="Sexual",
                source=RaiPolicyContentSource.COMPLETION,
                severity_threshold={
                    "High": ContentLevel.LOW,
                    "Medium": ContentLevel.MEDIUM,
                    "Low": ContentLevel.HIGH,
                }.get(config["guardrails"]["controls"]["content_harms"]["sexual"]),
                blocking=config["guardrails"]["controls"]["content_harms"]["action"]
                == "Block",
                enabled=config["guardrails"]["controls"]["content_harms"]["enabled"],
            ),
            RaiPolicyContentFilter(
                name="Selfharm",
                source=RaiPolicyContentSource.PROMPT,
                severity_threshold={
                    "High": ContentLevel.LOW,
                    "Medium": ContentLevel.MEDIUM,
                    "Low": ContentLevel.HIGH,
                }.get(config["guardrails"]["controls"]["content_harms"]["self_harm"]),
                blocking=config["guardrails"]["controls"]["content_harms"]["action"]
                == "Block",
                enabled=config["guardrails"]["controls"]["content_harms"]["enabled"],
            ),
            RaiPolicyContentFilter(
                name="Selfharm",
                source=RaiPolicyContentSource.COMPLETION,
                severity_threshold={
                    "High": ContentLevel.LOW,
                    "Medium": ContentLevel.MEDIUM,
                    "Low": ContentLevel.HIGH,
                }.get(config["guardrails"]["controls"]["content_harms"]["self_harm"]),
                blocking=config["guardrails"]["controls"]["content_harms"]["action"]
                == "Block",
                enabled=config["guardrails"]["controls"]["content_harms"]["enabled"],
            ),
            RaiPolicyContentFilter(
                name="Violence",
                source=RaiPolicyContentSource.PROMPT,
                severity_threshold={
                    "High": ContentLevel.LOW,
                    "Medium": ContentLevel.MEDIUM,
                    "Low": ContentLevel.HIGH,
                }.get(config["guardrails"]["controls"]["content_harms"]["violence"]),
                blocking=config["guardrails"]["controls"]["content_harms"]["action"]
                == "Block",
                enabled=config["guardrails"]["controls"]["content_harms"]["enabled"],
            ),
            RaiPolicyContentFilter(
                name="Violence",
                source=RaiPolicyContentSource.COMPLETION,
                severity_threshold={
                    "High": ContentLevel.LOW,
                    "Medium": ContentLevel.MEDIUM,
                    "Low": ContentLevel.HIGH,
                }.get(config["guardrails"]["controls"]["content_harms"]["violence"]),
                blocking=config["guardrails"]["controls"]["content_harms"]["action"]
                == "Block",
                enabled=config["guardrails"]["controls"]["content_harms"]["enabled"],
            ),
        ]
    )

    # Add Profanity Filter (Prompt & Completion)
    content_filters.extend(
        [
            RaiPolicyContentFilter(
                name="Profanity",
                source=RaiPolicyContentSource.PROMPT,
                blocking=config["guardrails"]["controls"]["profanity"]["action"]
                == "Block",
                enabled=config["guardrails"]["controls"]["profanity"]["enabled"],
            ),
            RaiPolicyContentFilter(
                name="Profanity",
                source=RaiPolicyContentSource.COMPLETION,
                blocking=config["guardrails"]["controls"]["profanity"]["action"]
                == "Block",
                enabled=config["guardrails"]["controls"]["profanity"]["enabled"],
            ),
        ]
    )

    # Add protected material filters for both text and code
    content_filters.extend(
        [
            RaiPolicyContentFilter(
                name="Protected Material Text",
                source=RaiPolicyContentSource.PROMPT,
                blocking=config["guardrails"]["controls"]["protected_materials"][
                    "action"
                ]
                == "Block",
                enabled=config["guardrails"]["controls"]["protected_materials"]["text"],
            ),
            RaiPolicyContentFilter(
                name="Protected Material Text",
                source=RaiPolicyContentSource.COMPLETION,
                blocking=config["guardrails"]["controls"]["protected_materials"][
                    "action"
                ]
                == "Block",
                enabled=config["guardrails"]["controls"]["protected_materials"]["text"],
            ),
            RaiPolicyContentFilter(
                name="Protected Material Code",
                source=RaiPolicyContentSource.PROMPT,
                blocking=config["guardrails"]["controls"]["protected_materials"][
                    "action"
                ]
                == "Block",
                enabled=config["guardrails"]["controls"]["protected_materials"]["code"],
            ),
            RaiPolicyContentFilter(
                name="Protected Material Code",
                source=RaiPolicyContentSource.COMPLETION,
                blocking=config["guardrails"]["controls"]["protected_materials"][
                    "action"
                ]
                == "Block",
                enabled=config["guardrails"]["controls"]["protected_materials"]["code"],
            ),
        ]
    )

    # Create the RAI Policy object with the defined content filters
    rai_policy = RaiPolicy(
        properties=RaiPolicyProperties(
            mode=RaiPolicyMode.BLOCKING,
            base_policy_name="Microsoft.Default",
            content_filters=content_filters,
        )
    )

    # Deploy the policy resource via Azure Management REST endpoint
    deployed_policy = mgmt_client.rai_policies.create_or_update(
        resource_group_name=resource_group_name,
        account_name=account_name,
        rai_policy_name=policy_name,
        rai_policy=rai_policy,
    )

    print(
        f"✅ RAI Policy deployed successfully. Resource ID:\n   {deployed_policy.id}\n"
    )
    return deployed_policy.id


def create_or_update_agent(
    project_client: AIProjectClient,
    config: dict,
    llm_model_deployment_name: str,
    policy_arm_id: str,
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

    rai_config = RaiConfig(rai_policy_name=policy_arm_id)

    try:
        print(f"   ✨ Creating or updating agent: {agent_name}")
        agent = project_client.agents.create_version(
            agent_name=agent_name,
            definition=PromptAgentDefinition(
                model=llm_model_deployment_name,
                instructions=system_prompt,
                rai_config=rai_config,
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

        # Create or update the RAI policy and get its ARM resource ID
        policy_arm_id = create_or_update_rai_policy(
            credential, subscription_id, resource_group_name, account_name, config
        )

        with AIProjectClient(
            endpoint=project_endpoint, credential=credential
        ) as project_client:

            print(f"Connected to Azure AI Foundry project at: {project_endpoint}")
            agent = create_or_update_agent(
                project_client, config, llm_model_deployment_name, policy_arm_id
            )

        print("\n✨ Agent deployment completed successfully!")
        return 0

    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
