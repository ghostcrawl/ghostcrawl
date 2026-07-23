from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .batch_scrape_request_behavior_actions import BatchScrapeRequest_behavior_actions
    from .batch_scrape_request_engine import BatchScrapeRequest_engine
    from .batch_scrape_request_extraction_strategy import BatchScrapeRequest_extraction_strategy
    from .batch_scrape_request_identity_country import BatchScrapeRequest_identity_country
    from .batch_scrape_request_language import BatchScrapeRequest_language
    from .batch_scrape_request_output_format import BatchScrapeRequest_output_format
    from .batch_scrape_request_profile import BatchScrapeRequest_profile

@dataclass
class BatchScrapeRequest(AdditionalDataHolder, Parsable):
    """
    Request body for POST /v1/scrape/batch. Accepts 1–20 URLs and a concurrency cap 1–10. All other fields mirror the shared scrape params from ScrapeBody and are applied uniformly to every URL in the batch.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The concurrency property
    concurrency: Optional[int] = 3
    from .batch_scrape_request_engine import BatchScrapeRequest_engine

    # The engine property
    engine: Optional[BatchScrapeRequest_engine] = BatchScrapeRequest_engine("auto")
    from .batch_scrape_request_output_format import BatchScrapeRequest_output_format

    # The output_format property
    output_format: Optional[BatchScrapeRequest_output_format] = BatchScrapeRequest_output_format("html")
    # The scroll_steps property
    scroll_steps: Optional[int] = 3
    # The scroll_to_bottom property
    scroll_to_bottom: Optional[bool] = False
    # The behavior_actions property
    behavior_actions: Optional[BatchScrapeRequest_behavior_actions] = None
    # The extraction_strategy property
    extraction_strategy: Optional[BatchScrapeRequest_extraction_strategy] = None
    # The identity_country property
    identity_country: Optional[BatchScrapeRequest_identity_country] = None
    # The language property
    language: Optional[BatchScrapeRequest_language] = None
    # The profile property
    profile: Optional[BatchScrapeRequest_profile] = None
    # The urls property
    urls: Optional[list[str]] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> BatchScrapeRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: BatchScrapeRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return BatchScrapeRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .batch_scrape_request_behavior_actions import BatchScrapeRequest_behavior_actions
        from .batch_scrape_request_engine import BatchScrapeRequest_engine
        from .batch_scrape_request_extraction_strategy import BatchScrapeRequest_extraction_strategy
        from .batch_scrape_request_identity_country import BatchScrapeRequest_identity_country
        from .batch_scrape_request_language import BatchScrapeRequest_language
        from .batch_scrape_request_output_format import BatchScrapeRequest_output_format
        from .batch_scrape_request_profile import BatchScrapeRequest_profile

        from .batch_scrape_request_behavior_actions import BatchScrapeRequest_behavior_actions
        from .batch_scrape_request_engine import BatchScrapeRequest_engine
        from .batch_scrape_request_extraction_strategy import BatchScrapeRequest_extraction_strategy
        from .batch_scrape_request_identity_country import BatchScrapeRequest_identity_country
        from .batch_scrape_request_language import BatchScrapeRequest_language
        from .batch_scrape_request_output_format import BatchScrapeRequest_output_format
        from .batch_scrape_request_profile import BatchScrapeRequest_profile

        fields: dict[str, Callable[[Any], None]] = {
            "behavior_actions": lambda n : setattr(self, 'behavior_actions', n.get_object_value(BatchScrapeRequest_behavior_actions)),
            "concurrency": lambda n : setattr(self, 'concurrency', n.get_int_value()),
            "engine": lambda n : setattr(self, 'engine', n.get_enum_value(BatchScrapeRequest_engine)),
            "extraction_strategy": lambda n : setattr(self, 'extraction_strategy', n.get_object_value(BatchScrapeRequest_extraction_strategy)),
            "identity_country": lambda n : setattr(self, 'identity_country', n.get_object_value(BatchScrapeRequest_identity_country)),
            "language": lambda n : setattr(self, 'language', n.get_object_value(BatchScrapeRequest_language)),
            "output_format": lambda n : setattr(self, 'output_format', n.get_enum_value(BatchScrapeRequest_output_format)),
            "profile": lambda n : setattr(self, 'profile', n.get_object_value(BatchScrapeRequest_profile)),
            "scroll_steps": lambda n : setattr(self, 'scroll_steps', n.get_int_value()),
            "scroll_to_bottom": lambda n : setattr(self, 'scroll_to_bottom', n.get_bool_value()),
            "urls": lambda n : setattr(self, 'urls', n.get_collection_of_primitive_values(str)),
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
        writer.write_int_value("concurrency", self.concurrency)
        writer.write_enum_value("engine", self.engine)
        writer.write_object_value("extraction_strategy", self.extraction_strategy)
        writer.write_object_value("identity_country", self.identity_country)
        writer.write_object_value("language", self.language)
        writer.write_enum_value("output_format", self.output_format)
        writer.write_object_value("profile", self.profile)
        writer.write_int_value("scroll_steps", self.scroll_steps)
        writer.write_bool_value("scroll_to_bottom", self.scroll_to_bottom)
        writer.write_collection_of_primitive_values("urls", self.urls)
        writer.write_additional_data_value(self.additional_data)
    

