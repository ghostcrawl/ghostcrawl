from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .content_request_identity_member1 import ContentRequest_identityMember1

@dataclass
class ContentRequest_identity(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes ContentRequest_identityMember1, str
    """
    # Composed type representation for type ContentRequest_identityMember1
    content_request_identity_member1: Optional[ContentRequest_identityMember1] = None
    # Composed type representation for type str
    string: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ContentRequest_identity:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ContentRequest_identity
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = ContentRequest_identity()
        if string_value := parse_node.get_str_value():
            result.string = string_value
        else:
            from .content_request_identity_member1 import ContentRequest_identityMember1

            result.content_request_identity_member1 = ContentRequest_identityMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .content_request_identity_member1 import ContentRequest_identityMember1

        if self.content_request_identity_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.content_request_identity_member1)
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
            writer.write_object_value(None, self.content_request_identity_member1)
    

