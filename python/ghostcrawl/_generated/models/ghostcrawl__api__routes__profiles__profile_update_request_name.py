from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .ghostcrawl__api__routes__profiles__profile_update_request_3fd814b2 import Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_3fd814b2

@dataclass
class Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_name(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_3fd814b2, str
    """
    # Composed type representation for type Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_3fd814b2
    ghostcrawl__api__routes__profiles__profile_update_request_name_member1: Optional[Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_3fd814b2] = None
    # Composed type representation for type str
    string: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_name:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_name
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_name()
        if string_value := parse_node.get_str_value():
            result.string = string_value
        else:
            from .ghostcrawl__api__routes__profiles__profile_update_request_3fd814b2 import Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_3fd814b2

            result.ghostcrawl__api__routes__profiles__profile_update_request_name_member1 = Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_3fd814b2()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .ghostcrawl__api__routes__profiles__profile_update_request_3fd814b2 import Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_3fd814b2

        if self.ghostcrawl__api__routes__profiles__profile_update_request_name_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.ghostcrawl__api__routes__profiles__profile_update_request_name_member1)
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
            writer.write_object_value(None, self.ghostcrawl__api__routes__profiles__profile_update_request_name_member1)
    

