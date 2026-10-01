import os
import asyncio
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from agent_framework.foundry import FoundryAgent
from agent_framework import Message, Content

# =============================================================================
# CONFIGURATION & INITIALIZATION
# =============================================================================

# You can use an environment variable or hardcode your project endpoint
endpoint = os.getenv("PROJECT_ENDPOINT")
agent_name = os.getenv("AGENT_NAME")

# Initialize Project Client & OpenAI Client
credential = DefaultAzureCredential()
project_client = AIProjectClient(endpoint=endpoint, credential=credential)

# =============================================================================
# AGENT
# =============================================================================


def create_agent():
    # 1. Wrap your pre-deployed Foundry project agents using FoundryChatClient & Agent
    agent = FoundryAgent(
        project_endpoint=endpoint,
        agent_name=agent_name,
        credential=credential,
    )

    return agent


def image_payload(image_path_input: str) -> Content | None:
    if not image_path_input:
        return None

    image_path = Path(image_path_input)
    if not image_path.exists():
        print(
            f"⚠️ Warning: Image not found at '{image_path_input}'. Proceeding text-only."
        )
        return None

    print(f"📷 Reading and attaching local image: {image_path.resolve()}")
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    ext = image_path.suffix.lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg"

    return Content.from_data(data=image_bytes, media_type=media_type)


# Microsoft Agent Frame is built entirely on async programming.
# agent.run() is an async method, so you need to run it in an async context.
async def run_agent(agent):
    print("Interactive workflow-agent mode started. Type 'exit' or 'quit' to stop.\n")

    # Create a server-side session to keep conversation history across turns
    session = await agent.create_conversation()
    print(f"Started session ID: {session}")

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

        image_path_input = input("Local image path (leave blank if none): ").strip()

        try:
            print("\n[AGENT] Executing pipeline...")

            # Construct the message payload using MAF's Content builders
            contents = [Content.from_text(text=user_message_text)]

            # If a local image path is provided, create an image content payload
            if image_path_input:
                image_content = image_payload(image_path_input)
                if image_content:
                    contents.append(image_content)

            # Wrap into an official MAF Message object
            message = Message(role="user", contents=contents)

            # Run the workflow-agent directly using standard agent execution
            result = await agent.run(message, session=session)

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
        agent = create_agent()
        asyncio.run(run_agent(agent))
        return 0
    except Exception as e:
        print(f"\n❌ Execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    main()
