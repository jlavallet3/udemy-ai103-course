import os
from azure.ai.contentunderstanding import ContentUnderstandingClient, to_llm_input
from azure.identity import DefaultAzureCredential
from agent_framework import tool


class AzureContentUnderstandingService:
    def __init__(self, cu_client):
        self.cu_client = cu_client

    def analyze_content(self, file_path, analyzer_id):
        if not self.cu_client:
            return "ERROR: Content Understanding service is not configured."

        print(
            f"[CONTENT UNDERSTANDING] Analyzing '{file_path}' using analyzer: '{analyzer_id}'"
        )

        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
        except FileNotFoundError:
            return f"ERROR: File not found at '{file_path}'"
        except Exception as error:
            return f"ERROR reading file: {error}"

        try:
            # Content Understanding long-running operation for binary inputs
            poller = self.cu_client.begin_analyze_binary(
                analyzer_id=analyzer_id,
                binary_input=file_data,
                content_type="application/octet-stream",
            )
            result = poller.result()

            # to_llm_input automatically translates AnalysisResult into a neat format
            # containing YAML front-matter fields and markdown content body.
            llm_formatted_output = to_llm_input(result)

            return llm_formatted_output

        except Exception as error:
            print(f"[CONTENT UNDERSTANDING] Error: {error}")
            return f"ERROR analyzing content: {error}"


@tool
def analyze_content_with_understanding(
    file_path: str, analyzer_id: str = "prebuilt-fileSearch"
) -> str:
    print(
        f"\n🛠️ [LOCAL TOOL EXECUTION] Dispatching to AzureContentUnderstandingService with analyzer '{analyzer_id}'..."
    )

    foundry_endpoint = os.getenv("FOUNDRY_ENDPOINT")
    credential = DefaultAzureCredential()

    cu_client = ContentUnderstandingClient(
        endpoint=foundry_endpoint,
        credential=credential,
    )

    cu_service = AzureContentUnderstandingService(cu_client=cu_client)

    return cu_service.analyze_content(file_path, analyzer_id=analyzer_id)
