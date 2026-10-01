import os
import sys
from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.identity import DefaultAzureCredential


def main() -> int:
    print("Setting up Content Understanding service...")
    print("=" * 60)

    foundry_endpoint = os.getenv("FOUNDRY_ENDPOINT")
    credential = DefaultAzureCredential()

    cu_client = ContentUnderstandingClient(
        endpoint=foundry_endpoint,
        credential=credential,
    )

    model_deployments = {
        "gpt-4.1": "courseunit647-llm-deploy",  # Maps the invoice/complex prebuilt requirement
        "gpt-4.1-mini": "courseunit647-llm-deploy",  # Maps the image/read/voice prebuilt requirement
        "text-embedding-3-large": "courseunit647-embedding-deploy",  # Maps the embedding prebuilt requirement
    }
    # model_deployments = {
    #     "gpt-5-mini": "courseunit647-llm-deploy",  # Maps the invoice/complex prebuilt requirement
    #     "text-embedding-3-large": "courseunit647-embedding-deploy",  # Maps the embedding prebuilt requirement
    # }

    print("Updating default model deployment mappings...")
    cu_client.update_defaults(model_deployments=model_deployments)

    print("Content Understanding service setup complete.")


if __name__ == "__main__":
    sys.exit(main())
