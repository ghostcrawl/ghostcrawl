from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .upload_body_profile_id_member1 import UploadBody_profile_idMember1

@dataclass
class UploadBody_profile_id(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes str, UploadBody_profile_idMember1
    """
    # Composed type representation for type str
    string: Optional[str] = None
    # Composed type representation for type UploadBody_profile_idMember1
    upload_body_profile_id_member1: Optional[UploadBody_profile_idMember1] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> UploadBody_profile_id:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: UploadBody_profile_id
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = UploadBody_profile_id()
        if string_value := parse_node.get_str_value():
            result.string = string_value
        else:
            from .upload_body_profile_id_member1 import UploadBody_profile_idMember1

            result.upload_body_profile_id_member1 = UploadBody_profile_idMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .upload_body_profile_id_member1 import UploadBody_profile_idMember1

        if self.upload_body_profile_id_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.upload_body_profile_id_member1)
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
            writer.write_object_value(None, self.upload_body_profile_id_member1)
    

