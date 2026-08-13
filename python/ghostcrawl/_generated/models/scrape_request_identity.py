from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .scrape_request_identity_member1 import ScrapeRequest_identityMember1

@dataclass
class ScrapeRequest_identity(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes ScrapeRequest_identityMember1, str
    """
    # Composed type representation for type ScrapeRequest_identityMember1
    scrape_request_identity_member1: Optional[ScrapeRequest_identityMember1] = None
    # Composed type representation for type str
    string: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ScrapeRequest_identity:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ScrapeRequest_identity
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = ScrapeRequest_identity()
        if string_value := parse_node.get_str_value():
            result.string = string_value
        else:
            from .scrape_request_identity_member1 import ScrapeRequest_identityMember1

            result.scrape_request_identity_member1 = ScrapeRequest_identityMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .scrape_request_identity_member1 import ScrapeRequest_identityMember1

        if self.scrape_request_identity_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.scrape_request_identity_member1)
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
            writer.write_object_value(None, self.scrape_request_identity_member1)
    

