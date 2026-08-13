from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .scrape_page_result import ScrapePageResult
    from .scrape_result_format import ScrapeResult_format
    from .scrape_result_identity_id import ScrapeResult_identity_id
    from .scrape_result_markdown import ScrapeResult_markdown
    from .scrape_result_status import ScrapeResult_status
    from .scrape_result_token_estimate import ScrapeResult_token_estimate
    from .scrape_result_warnings import ScrapeResult_warnings

@dataclass
class ScrapeResult(AdditionalDataHolder, Parsable):
    """
    POST /v1/scrape 200 response body. Documents the customer-facing shape so the OpenAPI 200 schema is no longer an empty ``{}`` (Kiota/typed SDKs need a named schema). ``extra="allow"`` keeps it forward-compatible with the markdown envelope (``format``/``markdown``/ ``chunks``/``citations``/``token_estimate``/``estimated_llm_input_tokens``) and the html envelope (``results``/``identity_id``/``identity_ids``/ ``identities_used``) without over-constraining the route (which returns a JSONResponse, so this model documents but does not coerce the body).
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # Output format when a non-default format was requested.
    format: Optional[ScrapeResult_format] = None
    # Generated identity id (single-identity path).
    identity_id: Optional[ScrapeResult_identity_id] = None
    # Concatenated Markdown (format=markdown path).
    markdown: Optional[ScrapeResult_markdown] = None
    # Per-URL results (html/default path).
    results: Optional[list[ScrapePageResult]] = None
    # Aggregate run status (e.g. completed / partial / failed).
    status: Optional[ScrapeResult_status] = None
    # Estimated token count of the markdown output.
    token_estimate: Optional[ScrapeResult_token_estimate] = None
    # Non-fatal warnings (e.g. host-identity fallback).
    warnings: Optional[ScrapeResult_warnings] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ScrapeResult:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ScrapeResult
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ScrapeResult()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .scrape_page_result import ScrapePageResult
        from .scrape_result_format import ScrapeResult_format
        from .scrape_result_identity_id import ScrapeResult_identity_id
        from .scrape_result_markdown import ScrapeResult_markdown
        from .scrape_result_status import ScrapeResult_status
        from .scrape_result_token_estimate import ScrapeResult_token_estimate
        from .scrape_result_warnings import ScrapeResult_warnings

        from .scrape_page_result import ScrapePageResult
        from .scrape_result_format import ScrapeResult_format
        from .scrape_result_identity_id import ScrapeResult_identity_id
        from .scrape_result_markdown import ScrapeResult_markdown
        from .scrape_result_status import ScrapeResult_status
        from .scrape_result_token_estimate import ScrapeResult_token_estimate
        from .scrape_result_warnings import ScrapeResult_warnings

        fields: dict[str, Callable[[Any], None]] = {
            "format": lambda n : setattr(self, 'format', n.get_object_value(ScrapeResult_format)),
            "identity_id": lambda n : setattr(self, 'identity_id', n.get_object_value(ScrapeResult_identity_id)),
            "markdown": lambda n : setattr(self, 'markdown', n.get_object_value(ScrapeResult_markdown)),
            "results": lambda n : setattr(self, 'results', n.get_collection_of_object_values(ScrapePageResult)),
            "status": lambda n : setattr(self, 'status', n.get_object_value(ScrapeResult_status)),
            "token_estimate": lambda n : setattr(self, 'token_estimate', n.get_object_value(ScrapeResult_token_estimate)),
            "warnings": lambda n : setattr(self, 'warnings', n.get_object_value(ScrapeResult_warnings)),
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
        writer.write_object_value("format", self.format)
        writer.write_object_value("identity_id", self.identity_id)
        writer.write_object_value("markdown", self.markdown)
        writer.write_collection_of_object_values("results", self.results)
        writer.write_object_value("status", self.status)
        writer.write_object_value("token_estimate", self.token_estimate)
        writer.write_object_value("warnings", self.warnings)
        writer.write_additional_data_value(self.additional_data)
    

