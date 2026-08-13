from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .scrape_request_timeout_ms_member1 import ScrapeRequest_timeout_msMember1

@dataclass
class ScrapeRequest_timeout_ms(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes int, ScrapeRequest_timeout_msMember1
    """
    # Composed type representation for type int
    integer: Optional[int] = None
    # Composed type representation for type ScrapeRequest_timeout_msMember1
    scrape_request_timeout_ms_member1: Optional[ScrapeRequest_timeout_msMember1] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ScrapeRequest_timeout_ms:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ScrapeRequest_timeout_ms
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = ScrapeRequest_timeout_ms()
        if integer_value := parse_node.get_int_value():
            result.integer = integer_value
        else:
            from .scrape_request_timeout_ms_member1 import ScrapeRequest_timeout_msMember1

            result.scrape_request_timeout_ms_member1 = ScrapeRequest_timeout_msMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .scrape_request_timeout_ms_member1 import ScrapeRequest_timeout_msMember1

        if self.scrape_request_timeout_ms_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.scrape_request_timeout_ms_member1)
        return {}
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        if self.integer:
            writer.write_int_value(None, self.integer)
        else:
            writer.write_object_value(None, self.scrape_request_timeout_ms_member1)
    

