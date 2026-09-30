import os
import yaml
from pathlib import Path
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import OpenAI

# =============================================================================
# CONFIGURATION & INITIALIZATION
# =============================================================================

# Pull settings from environment variables or drop in defaults
endpoint = os.getenv("OPENAI_ENDPOINT")
deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

config_path = Path("config.yaml")
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

# Azure AD token provider for seamless passwordless auth
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)

# Initialize standard OpenAI client pointed at Azure endpoint
client = OpenAI(
    base_url=endpoint,
    api_key=token_provider,  # Pass the dynamic token callback directly as api_key
)

# =============================================================================
# MAIN INTERACTIVE LOOP
# =============================================================================


def interactive_loop():
    print("Interactive mode started. Type 'exit' or 'quit' to stop.")

    # Maintain conversation history across user inputs
    conversation_history = [{"role": "system", "content": config["system_prompt"]}]

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

        # Append latest user prompt to history
        conversation_history.append({"role": "user", "content": user_message_text})

        print("\n[AGENT] Processing message with LLM...")

        try:
            # Send entire chat history so the model keeps context
            response = client.chat.completions.create(
                model=deployment_name, messages=conversation_history
            )

            assistant_reply = response.choices[0].message.content

            print("\n" + "=" * 50)
            print("ASSISTANT REPLY:")
            print("=" * 50)
            print(assistant_reply)
            print("=" * 50)

            # Persist assistant's reply in local turn history
            conversation_history.append(
                {"role": "assistant", "content": assistant_reply}
            )

        except Exception as e:
            print(f"ERROR: Failed to get response from model: {e}")


if __name__ == "__main__":
    interactive_loop()
