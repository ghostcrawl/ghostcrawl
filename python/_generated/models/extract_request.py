from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .extract_request_behavior_actions import ExtractRequest_behavior_actions
    from .extract_request_engine import ExtractRequest_engine
    from .extract_request_identity_country import ExtractRequest_identity_country
    from .extract_request_language import ExtractRequest_language
    from .extract_request_prompt import ExtractRequest_prompt
    from .extract_request_url import ExtractRequest_url
    from .extract_request_urls import ExtractRequest_urls

@dataclass
class ExtractRequest(AdditionalDataHolder, Parsable):
    """
    POST /v1/extract request body, schema-driven extraction (deterministic) + bring-your-own-model extraction. Two extraction modes: - Deterministic (default, model_provider absent): CSS/regex/keyword extraction. Requires 'schema'. Returns {"url","data","token_estimate"}. - Bring-your-own-model (model_provider present): GhostCrawl fetches and prepares clean Markdown; your connected model performs the semantic extraction (you are not billed for model inference here, only the request quota). Returns {"urls","data","token_estimate"}. Security notes: - The 'schema' field is validated before any fetch (fail-fast input guard). - URLs are validated against private, loopback, and metadata targets before any fetch. - Error responses never echo the schema body, fetched content, or model credentials. - model_provider.api_key is request-scoped only: never persisted, logged, or returned in any response body or error message.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    from .extract_request_engine import ExtractRequest_engine

    # Engine override: auto (default) | chrome | firefox | webkit.
    engine: Optional[ExtractRequest_engine] = ExtractRequest_engine("auto")
    # BYO behavior: trusted-input actions replayed on the loaded page instead of the built-in human session. Sanitized + bounded server-side (max 256 actions). Available on every tier.
    behavior_actions: Optional[ExtractRequest_behavior_actions] = None
    # Optional two-letter country code to pin (geo-filters the exit and derives timezone; tier-gated). Omitted = timezone follows the exit.
    identity_country: Optional[ExtractRequest_identity_country] = None
    # Optional browser language tag (e.g. 'en-US','es-ES'). Sets the identity's locale and language headers coherently, independent of the exit country. Available on every tier.
    language: Optional[ExtractRequest_language] = None
    # Free-form extraction instruction for BYO-LLM mode. Allowed without a schema (schema-less prose extraction). Ignored in deterministic mode (model_provider absent).
    prompt: Optional[ExtractRequest_prompt] = None
    # URL to fetch and extract from (single-URL mode). Required when 'urls' is not provided.
    url: Optional[ExtractRequest_url] = None
    # Multi-URL cross-page aggregation (bring-your-own-model mode only). Each URL is fetched and converted to clean Markdown, then concatenated with per-URL delimiter headers; one aggregated model call extracts across all pages. Bounded to ≤10 URLs. Cannot be combined with 'url' when both are provided.
    urls: Optional[ExtractRequest_urls] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ExtractRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ExtractRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ExtractRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .extract_request_behavior_actions import ExtractRequest_behavior_actions
        from .extract_request_engine import ExtractRequest_engine
        from .extract_request_identity_country import ExtractRequest_identity_country
        from .extract_request_language import ExtractRequest_language
        from .extract_request_prompt import ExtractRequest_prompt
        from .extract_request_url import ExtractRequest_url
        from .extract_request_urls import ExtractRequest_urls

        from .extract_request_behavior_actions import ExtractRequest_behavior_actions
        from .extract_request_engine import ExtractRequest_engine
        from .extract_request_identity_country import ExtractRequest_identity_country
        from .extract_request_language import ExtractRequest_language
        from .extract_request_prompt import ExtractRequest_prompt
        from .extract_request_url import ExtractRequest_url
        from .extract_request_urls import ExtractRequest_urls

        fields: dict[str, Callable[[Any], None]] = {
            "behavior_actions": lambda n : setattr(self, 'behavior_actions', n.get_object_value(ExtractRequest_behavior_actions)),
            "engine": lambda n : setattr(self, 'engine', n.get_enum_value(ExtractRequest_engine)),
            "identity_country": lambda n : setattr(self, 'identity_country', n.get_object_value(ExtractRequest_identity_country)),
            "language": lambda n : setattr(self, 'language', n.get_object_value(ExtractRequest_language)),
            "prompt": lambda n : setattr(self, 'prompt', n.get_object_value(ExtractRequest_prompt)),
            "url": lambda n : setattr(self, 'url', n.get_object_value(ExtractRequest_url)),
            "urls": lambda n : setattr(self, 'urls', n.get_object_value(ExtractRequest_urls)),
        }
        return fields
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        writer.write_object_value("behavior_actions", self.behavior_actions)
        writer.write_enum_value("engine", self.engine)
        writer.write_object_value("identity_country", self.identity_country)
        writer.write_object_value("language", self.language)
        writer.write_object_value("prompt", self.prompt)
        writer.write_object_value("url", self.url)
        writer.write_object_value("urls", self.urls)
        writer.write_additional_data_value(self.additional_data)
    

