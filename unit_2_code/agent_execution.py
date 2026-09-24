import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# =============================================================================
# CONFIGURATION & INITIALIZATION
# =============================================================================

# You can use an environment variable or hardcode your project endpoint
endpoint = os.getenv("PROJECT_ENDPOINT")
agent_name = os.getenv("AGENT_NAME")
agent_version = os.getenv("AGENT_VERSION")

# Initialize Project Client & OpenAI Client
project_client = AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(),
)
openai_client = project_client.get_openai_client()

# =============================================================================
# MAIN INTERACTIVE LOOP
# =============================================================================


def interactive_loop():
    print("Interactive mode started. Type 'exit' or 'quit' to stop.")

    # 1. Initialize a new conversation thread ONCE before the loop
    conversation = openai_client.conversations.create()
    conversation_id = conversation.id
    print(f"Started conversation ID: {conversation_id}")

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

        print("\n[AGENT] Processing message with agent...")

        try:
            # 2. Append the user message item directly to the active conversation
            openai_client.conversations.items.create(
                conversation_id=conversation_id,
                items=[
                    {
                        "type": "message",
                        "role": "user",
                        "content": user_message_text,
                    }
                ],
            )

            # 3. Generate a response referencing the conversation ID explicitly
            response = openai_client.responses.create(
                conversation=conversation_id,
                extra_body={
                    "agent_reference": {
                        "name": agent_name,
                        "version": agent_version,
                        "type": "agent_reference",
                    }
                },
            )

            print("\n" + "=" * 50)
            print("ASSISTANT REPLY:")
            print("=" * 50)
            print(response.output_text)
            print("=" * 50)

        except Exception as e:
            print(f"ERROR: Failed to get response from model: {e}")


if __name__ == "__main__":
    interactive_loop()
