import os
import asyncio
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from agent_framework.orchestrations import MagenticBuilder
from agent_framework.foundry import FoundryAgent

# =============================================================================
# CONFIGURATION & INITIALIZATION
# =============================================================================

# You can use an environment variable or hardcode your project endpoint
endpoint = os.getenv("PROJECT_ENDPOINT")
manager_agent_name = os.getenv("MANAGER_AGENT_NAME")
extractor_agent_name = os.getenv("EXTRACTOR_AGENT_NAME")
analyst_agent_name = os.getenv("ANALYST_AGENT_NAME")

# Initialize Project Client & OpenAI Client
credential = DefaultAzureCredential()
project_client = AIProjectClient(endpoint=endpoint, credential=credential)

# =============================================================================
# WORKFLOW
# =============================================================================


def create_workflow():
    # 1. Wrap your pre-deployed Foundry project agents using FoundryChatClient & Agent
    manager_agent = FoundryAgent(
        project_endpoint=endpoint,
        agent_name=manager_agent_name,
        credential=credential,
    )
    extractor_agent = FoundryAgent(
        project_endpoint=endpoint,
        agent_name=extractor_agent_name,
        credential=credential,
    )
    analyst_agent = FoundryAgent(
        project_endpoint=endpoint,
        agent_name=analyst_agent_name,
        credential=credential,
    )

    # 2. Build the workflow
    workflow = MagenticBuilder(
        manager_agent=manager_agent,
        participants=[extractor_agent, analyst_agent],
        max_round_count=5,  # Maximum number of interaction rounds before the workflow terminates
        max_stall_count=3,  # Maximum number of consecutive rounds without progress before the workflow terminates
    ).build()

    # 3. Convert the workflow to an agent
    workflow_agent = workflow.as_agent(name="Content Pipeline Agent")

    return workflow_agent


# Microsoft Agent Frame is built entirely on async programming.
# agent.run() is an async method, so you need to run it in an async context.
async def run_workflow(agent):
    print("Interactive workflow-agent mode started. Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_message_text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not user_message_text:
            continue
        if user_message_text.lower() in ("exit", "quit"):
            print("Exiting interactive mode.")
            break

        try:
            print("\n[WORKFLOW AGENT] Executing pipeline...")

            # Run the workflow-agent directly using standard agent execution
            result = await agent.run(user_message_text)

            # The result object from an agent run typically contains a text property
            final_text = getattr(result, "text", str(result))

            print("\n" + "=" * 50)
            print("ASSISTANT REPLY:")
            print("=" * 50)
            print(final_text)
            print("=" * 50)

        except Exception as e:
            print(f"❌ ERROR during workflow execution: {e}")


def main() -> int:
    try:
        workflow_agent = create_workflow()
        asyncio.run(run_workflow(workflow_agent))
        return 0
    except Exception as e:
        print(f"\n❌ Execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    main()
