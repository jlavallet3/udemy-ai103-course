import os
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.core.credentials import AzureKeyCredential
from agent_framework import tool

# =============================================================================
# AZURE VISION SERVICE CLASS
# =============================================================================


class AzureVisionService:
    def __init__(self, vision_client):
        self.vision_client = vision_client

    def analyze_image(self, image_path):
        if not self.vision_client:
            return "ERROR: Vision service is not configured."

        print(f"[VISION] Analyzing image: {image_path}")

        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
        except FileNotFoundError:
            return f"ERROR: Image file not found at '{image_path}'"
        except Exception as error:
            return f"ERROR reading image file: {error}"

        try:
            # Note: Ensure VisualFeatures.CAPTION is also included if you want captions back
            result = self.vision_client.analyze(
                image_data=image_data,
                visual_features=[
                    VisualFeatures.CAPTION, # Not available in the current SDK version for australiaeast region
                    VisualFeatures.READ,
                    VisualFeatures.TAGS,
                ],
                language="en",
            )

            response_parts = []

            # 1. Handle Caption (if enabled/present)
            if hasattr(result, "caption") and result.caption:
                response_parts.append(
                    f"Image description: {result.caption.text} "
                    f"(confidence: {result.caption.confidence:.2f})"
                )
            else:
                response_parts.append("No caption generated for this image.")

            # 2. Handle Read / OCR Result (matching blocks -> lines -> text)
            # Checking both object dot-notation and dictionary fallback if using .as_dict()
            read_data = result.read if hasattr(result, "read") else None
            if read_data and getattr(read_data, "blocks", None):
                ocr_texts = []
                for block in read_data.blocks:
                    for line in block.lines:
                        ocr_texts.append(line.text)
                if ocr_texts:
                    response_parts.append(f"Text found in image: {' '.join(ocr_texts)}")
                else:
                    response_parts.append("No text found in this image.")
            else:
                response_parts.append("No text found in this image.")

            # 3. Handle Tags Result safely handling dict/object mapping
            tags_data = result.tags if hasattr(result, "tags") else None

            # Extract the actual list of tags whether it's a dict or SDK model
            tag_list = []
            if tags_data:
                if isinstance(tags_data, dict):
                    tag_list = tags_data.get("values", [])
                elif hasattr(tags_data, "values"):
                    # Check if 'values' is callable (the dict method) or an attribute list
                    val_attr = tags_data.values
                    if callable(val_attr):
                        # It's a dict-like object; try standard key lookup or call it safely
                        raw_dict = (
                            tags_data.as_dict()
                            if hasattr(tags_data, "as_dict")
                            else dict(tags_data)
                        )
                        tag_list = raw_dict.get("values", [])
                    else:
                        tag_list = val_attr

            if not tag_list:
                response_parts.append("No tags detected in this image.")
            else:
                tags_info = []
                for tag in tag_list:
                    # Handle both object attributes (.name) and dictionary keys (['name'])
                    name = tag.name if hasattr(tag, "name") else tag.get("name")
                    confidence = (
                        tag.confidence
                        if hasattr(tag, "confidence")
                        else tag.get("confidence", 0.0)
                    )
                    tags_info.append(f"{name} (confidence: {confidence:.2f})")

                response_parts.append(f"Tags detected: {', '.join(tags_info)}")

            return "\n".join(response_parts)

        except Exception as error:
            print(f"[VISION] Error: {error}")
            return f"ERROR analyzing image: {error}"


# =============================================================================
# INITIALIZE SERVICE & TOOL BINDING
# =============================================================================


@tool
def analyze_image_with_vision(image_path: str) -> str:
    print(f"\n🛠️ [LOCAL TOOL EXECUTION] Dispatching to AzureVisionService...")

    vision_endpoint = os.getenv("VISION_ENDPOINT")
    vision_key = os.getenv("VISION_KEY")

    vision_sdk_client = ImageAnalysisClient(
        endpoint=vision_endpoint, credential=AzureKeyCredential(vision_key)
    )

    vision_service = AzureVisionService(vision_client=vision_sdk_client)

    return vision_service.analyze_image(image_path)
