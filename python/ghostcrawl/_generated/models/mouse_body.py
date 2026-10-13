from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .mouse_body_ops import MouseBody_ops
    from .mouse_body_profile_id import MouseBody_profile_id
    from .mouse_body_session_id import MouseBody_session_id

@dataclass
class MouseBody(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The ops property
    ops: Optional[list[MouseBody_ops]] = None
    # The profile_id property
    profile_id: Optional[MouseBody_profile_id] = None
    # The session_id property
    session_id: Optional[MouseBody_session_id] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> MouseBody:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: MouseBody
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return MouseBody()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .mouse_body_ops import MouseBody_ops
        from .mouse_body_profile_id import MouseBody_profile_id
        from .mouse_body_session_id import MouseBody_session_id

        from .mouse_body_ops import MouseBody_ops
        from .mouse_body_profile_id import MouseBody_profile_id
        from .mouse_body_session_id import MouseBody_session_id

        fields: dict[str, Callable[[Any], None]] = {
            "ops": lambda n : setattr(self, 'ops', n.get_collection_of_object_values(MouseBody_ops)),
            "profile_id": lambda n : setattr(self, 'profile_id', n.get_object_value(MouseBody_profile_id)),
            "session_id": lambda n : setattr(self, 'session_id', n.get_object_value(MouseBody_session_id)),
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
        writer.write_collection_of_object_values("ops", self.ops)
        writer.write_object_value("profile_id", self.profile_id)
        writer.write_object_value("session_id", self.session_id)
        writer.write_additional_data_value(self.additional_data)
    

