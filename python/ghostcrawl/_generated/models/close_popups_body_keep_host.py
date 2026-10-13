from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .close_popups_body_keep_host_member1 import ClosePopupsBody_keep_hostMember1

@dataclass
class ClosePopupsBody_keep_host(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes ClosePopupsBody_keep_hostMember1, str
    """
    # Composed type representation for type ClosePopupsBody_keep_hostMember1
    close_popups_body_keep_host_member1: Optional[ClosePopupsBody_keep_hostMember1] = None
    # Composed type representation for type str
    string: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ClosePopupsBody_keep_host:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ClosePopupsBody_keep_host
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = ClosePopupsBody_keep_host()
        if string_value := parse_node.get_str_value():
            result.string = string_value
        else:
            from .close_popups_body_keep_host_member1 import ClosePopupsBody_keep_hostMember1

            result.close_popups_body_keep_host_member1 = ClosePopupsBody_keep_hostMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .close_popups_body_keep_host_member1 import ClosePopupsBody_keep_hostMember1

        if self.close_popups_body_keep_host_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.close_popups_body_keep_host_member1)
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
            writer.write_object_value(None, self.close_popups_body_keep_host_member1)
    

