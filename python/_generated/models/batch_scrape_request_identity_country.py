from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .batch_scrape_request_identity_country_member1 import BatchScrapeRequest_identity_countryMember1

@dataclass
class BatchScrapeRequest_identity_country(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes BatchScrapeRequest_identity_countryMember1, str
    """
    # Composed type representation for type BatchScrapeRequest_identity_countryMember1
    batch_scrape_request_identity_country_member1: Optional[BatchScrapeRequest_identity_countryMember1] = None
    # Composed type representation for type str
    string: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> BatchScrapeRequest_identity_country:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: BatchScrapeRequest_identity_country
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = BatchScrapeRequest_identity_country()
        if string_value := parse_node.get_str_value():
            result.string = string_value
        else:
            from .batch_scrape_request_identity_country_member1 import BatchScrapeRequest_identity_countryMember1

            result.batch_scrape_request_identity_country_member1 = BatchScrapeRequest_identity_countryMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .batch_scrape_request_identity_country_member1 import BatchScrapeRequest_identity_countryMember1

        if self.batch_scrape_request_identity_country_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.batch_scrape_request_identity_country_member1)
        return {}
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        if self.string:
            writer.write_str_value(None, self.string)
        else:
            writer.write_object_value(None, self.batch_scrape_request_identity_country_member1)
    

