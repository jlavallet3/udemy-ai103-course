import os
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from agent_framework import tool


class AzureDocumentIntelligenceService:
    def __init__(self, doc_client):
        self.doc_client = doc_client

    def analyze_document(self, document_path, model_id):
        if not self.doc_client:
            return "ERROR: Document Intelligence service is not configured."

        print(f"[DOC INTEL] Analyzing '{document_path}' using model: '{model_id}'")

        try:
            with open(document_path, "rb") as f:
                document_data = f.read()
        except FileNotFoundError:
            return f"ERROR: Document file not found at '{document_path}'"
        except Exception as error:
            return f"ERROR reading document file: {error}"

        try:
            # Dynamically pass the requested model ID (e.g., prebuilt-invoice, prebuilt-receipt, prebuilt-layout)
            poller = self.doc_client.begin_analyze_document(
                model_id=model_id,
                body=document_data,
                content_type="application/octet-stream",
            )
            result = poller.result()

            response_parts = [f"Successfully analyzed using model: {model_id}"]

            # Generic content fallback
            if hasattr(result, "content") and result.content:
                content_preview = result.content[:2000] + (
                    "..." if len(result.content) > 2000 else ""
                )
                response_parts.append(f"Content Preview:\n{content_preview}")

            # Specific prebuilt extractions (invoices, receipts, etc. return fields)
            if hasattr(result, "documents") and result.documents:
                response_parts.append(
                    f"Extracted {len(result.documents)} specialized document fields:"
                )
                for doc in result.documents:
                    response_parts.append(
                        f" - Document Type: {doc.doc_type} (Confidence: {doc.confidence:.2f})"
                    )
                    if hasattr(doc, "fields") and doc.fields:
                        for field_name, field_val in doc.fields.items():
                            val_content = getattr(field_val, "content", str(field_val))
                            response_parts.append(f"   * {field_name}: {val_content}")

            return "\n".join(response_parts)

        except Exception as error:
            print(f"[DOC INTEL] Error: {error}")
            return f"ERROR analyzing document: {error}"


@tool
def analyze_document_with_intelligence(
    document_path: str, model_id: str = "prebuilt-layout"
) -> str:
    """
    Analyzes a document using Azure AI Document Intelligence.

    Args:
        document_path: Path to the local file.
        model_id: The model to use. Options include:
                  - 'prebuilt-layout' (general text, structure, tables)
                  - 'prebuilt-invoice' (vendor, customer, line items, totals)
                  - 'prebuilt-receipt' (merchant name, transaction dates, prices)
                  - 'prebuilt-idDocument' (passports, driver licenses)
                  - 'prebuilt-tax.us.w2' (US W-2 tax forms)
    """
    print(
        f"\n🛠️ [LOCAL TOOL EXECUTION] Dispatching to AzureDocumentIntelligenceService with model '{model_id}'..."
    )

    doc_endpoint = os.getenv("DOC_INTEL_ENDPOINT")
    doc_key = os.getenv("DOC_INTEL_KEY")

    doc_sdk_client = DocumentIntelligenceClient(
        endpoint=doc_endpoint, credential=AzureKeyCredential(doc_key)
    )

    doc_service = AzureDocumentIntelligenceService(doc_client=doc_sdk_client)

    return doc_service.analyze_document(document_path, model_id=model_id)
