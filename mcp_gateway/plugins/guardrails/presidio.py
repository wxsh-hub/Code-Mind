import logging
from typing import Any, Dict, List, Optional, Tuple

from mcp import types
from mcp_gateway.plugins.base import GuardrailPlugin, PluginContext
from mcp_gateway.plugins.manager import register_plugin

logger = logging.getLogger(__name__)

DEFAULT_PII_ENTITIES = [
    "CREDIT_CARD",
    "IP_ADDRESS",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CRYPTO",
    "MEDICAL_LICENSE",
    "US_PASSPORT",
    "US_ITIN",
    "US_SSN",
]


@register_plugin
class PresidioGuardrailPlugin(GuardrailPlugin):
    """
    A guardrail that anonymizes PII using Presidio.
    """

    plugin_name = "presidio"

    def __init__(self):
        self.analyzer = None
        self.anonymizer = None
        self.pii_entities: List[str] = DEFAULT_PII_ENTITIES
        self.presidio_loaded: bool = False

    def load(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Loads configuration and initializes Presidio engines if available.
        Configuration options:
        - pii_entities: List of Presidio entity types to detect (default: DEFAULT_PII_ENTITIES)
        - enable_presidio: Explicitly enable/disable Presidio use (default: True if installed)
        """
        if config is None:
            config = {}

        self.pii_entities = config.get("pii_entities", DEFAULT_PII_ENTITIES)
        enable_presidio = config.get(
            "enable_presidio", True
        )  # Default to True if installed

        if not enable_presidio:
            logger.info(
                "Presidio processing is disabled for PresidioGuardrailPlugin via config."
            )
            self.presidio_loaded = False
            return

        # Attempt to load presidio libraries only when the plugin is actually enabled
        try:
            logger.info("Attempting to import Presidio libraries...")
            from presidio_anonymizer import AnonymizerEngine
            from presidio_analyzer import AnalyzerEngine

            # Initialize Presidio engines
            try:
                logger.info("Initializing Presidio Analyzer and Anonymizer...")
                self.analyzer = AnalyzerEngine()
                self.anonymizer = AnonymizerEngine()
                self.presidio_loaded = True
                logger.info(
                    f"Presidio initialized for PII anonymization. Detecting entities: {self.pii_entities}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to initialize Presidio engines: {e}", exc_info=True
                )
                self.presidio_loaded = False
        except ImportError:
            logger.warning(
                "Presidio libraries not found. Install with: pip install -e .[presidio]"
            )
            self.presidio_loaded = False

    def _pii_anonymizer(self, text: str) -> str:
        """Anonymizes PII in text using Presidio."""
        if not self.presidio_loaded or not self.analyzer or not self.anonymizer:
            logger.debug("Presidio not loaded or enabled, skipping PII anonymization.")
            return text
        try:
            analyzer_results = self.analyzer.analyze(
                text=text, language="en", entities=self.pii_entities
            )
            anonymized_result = self.anonymizer.anonymize(
                text=text, analyzer_results=analyzer_results
            )
            # Check if anonymization occurred
            if text != anonymized_result.text:
                logger.info(f"Anonymized PII content using Presidio.")
            return anonymized_result.text
        except Exception as e:
            logger.error(f"Error during Presidio PII anonymization: {e}", exc_info=True)
            return text  # Return original text on error

    def process_request(self, context: PluginContext) -> Optional[Dict[str, Any]]:
        """Processes request arguments, anonymizing PII in string values."""
        logger.debug(
            f"PresidioGuardrail processing request for {context.server_name}/{context.capability_name}"
        )
        if not context.arguments or not self.presidio_loaded:
            return context.arguments

        sanitized = False
        for key, value in context.arguments.items():
            if isinstance(value, str):
                cleaned = self._pii_anonymizer(value)
                if cleaned != value:
                    context.arguments[key] = cleaned
                    sanitized = True

        if sanitized:
            logger.info(
                f"Anonymized PII in request arguments for {context.server_name}/{context.capability_name}"
            )
        return context.arguments

    def process_response(self, context: PluginContext) -> Any:
        """
        Processes response data, applying PII anonymization to text content.
        Targets mcp.types.CallToolResult, resource reads, and GetPromptResult.
        """
        logger.debug(
            f"PresidioGuardrail processing response for {context.server_name}/{context.capability_name}"
        )
        response = context.response

        # --- Handle Tool Call Results ---
        if (
            isinstance(response, types.CallToolResult)
            and hasattr(response, "content")
            and response.content
        ):
            sanitized_content = []
            content_changed = False
            for content_item in response.content:
                if isinstance(content_item, types.TextContent):
                    original_text = content_item.text
                    sanitized_text = self._pii_anonymizer(original_text)
                    if original_text != sanitized_text:
                        content_changed = True
                    sanitized_content.append(
                        types.TextContent(type="text", text=sanitized_text)
                    )
                else:
                    sanitized_content.append(content_item)

            # Return new object only if changes were made
            if content_changed:
                logger.info(
                    f"Anonymized PII in CallToolResult content for {context.server_name}/{context.capability_name}"
                )
                return types.CallToolResult(
                    content=sanitized_content, isError=response.isError
                )
            else:
                return response  # Return original if no changes

        # --- Handle Resource Reads (Tuple[bytes, Optional[str]]) ---
        elif (
            isinstance(response, tuple)
            and len(response) == 2
            and isinstance(response[0], bytes)
        ):
            content_bytes, mime_type = response
            if mime_type and (
                "text" in mime_type or "json" in mime_type or "xml" in mime_type
            ):
                try:
                    original_text = content_bytes.decode("utf-8", errors="replace")
                    sanitized_text = self._pii_anonymizer(original_text)
                    if original_text != sanitized_text:
                        logger.info(
                            f"Anonymized PII in text-based resource response for {context.server_name}/{context.capability_name}"
                        )
                        sanitized_bytes = sanitized_text.encode("utf-8")
                        return sanitized_bytes, mime_type
                    else:
                        return (
                            content_bytes,
                            mime_type,
                        )  # Return original bytes if no changes
                except Exception as e:
                    logger.error(
                        f"Error sanitizing resource content with Presidio: {e}",
                        exc_info=True,
                    )
                    return content_bytes, mime_type
            else:
                return content_bytes, mime_type

        # --- Handle GetPromptResult ---
        elif isinstance(response, types.GetPromptResult) and response.messages:
            sanitized_messages = []
            message_changed = False
            for message in response.messages:
                if isinstance(message.content, types.TextContent):
                    original_text = message.content.text
                    sanitized_text = self._pii_anonymizer(original_text)
                    if original_text != sanitized_text:
                        message_changed = True
                    sanitized_content = types.TextContent(
                        type="text", text=sanitized_text
                    )
                    sanitized_messages.append(
                        types.PromptMessage(
                            role=message.role, content=sanitized_content
                        )
                    )
                else:
                    sanitized_messages.append(message)

            if message_changed:
                logger.info(
                    f"Anonymized PII in GetPromptResult messages for {context.server_name}/{context.capability_name}"
                )
                return types.GetPromptResult(
                    description=response.description, messages=sanitized_messages
                )
            else:
                return response  # Return original if no changes

        # --- Default: Return original response ---
        logger.debug(
            f"Response type {type(response)} not handled by PresidioGuardrailPlugin, returning original."
        )
        return response
