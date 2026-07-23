from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .extract_request_urls_member1 import ExtractRequest_urlsMember1

@dataclass
class ExtractRequest_urls(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes ExtractRequest_urlsMember1, list[str]
    """
    # Composed type representation for type ExtractRequest_urlsMember1
    extract_request_urls_member1: Optional[ExtractRequest_urlsMember1] = None
    # Composed type representation for type list[str]
    string: Optional[list[str]] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ExtractRequest_urls:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ExtractRequest_urls
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = ExtractRequest_urls()
        if string_value := parse_node.get_collection_of_primitive_values(str):
            result.string = string_value
        else:
            from .extract_request_urls_member1 import ExtractRequest_urlsMember1

            result.extract_request_urls_member1 = ExtractRequest_urlsMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .extract_request_urls_member1 import ExtractRequest_urlsMember1

        if self.extract_request_urls_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.extract_request_urls_member1)
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
            writer.write_collection_of_primitive_values(None, self.string)
        else:
            writer.write_object_value(None, self.extract_request_urls_member1)
    

