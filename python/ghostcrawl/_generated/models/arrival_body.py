from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .arrival_body_profile_id import ArrivalBody_profile_id
    from .arrival_body_referrer_shape import ArrivalBody_referrer_shape
    from .arrival_body_session_id import ArrivalBody_session_id

@dataclass
class ArrivalBody(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    from .arrival_body_referrer_shape import ArrivalBody_referrer_shape

    # The referrer_shape property
    referrer_shape: Optional[ArrivalBody_referrer_shape] = ArrivalBody_referrer_shape("origin")
    # The dest_url property
    dest_url: Optional[str] = None
    # The profile_id property
    profile_id: Optional[ArrivalBody_profile_id] = None
    # The session_id property
    session_id: Optional[ArrivalBody_session_id] = None
    # The source_title property
    source_title: Optional[str] = None
    # The source_url property
    source_url: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ArrivalBody:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ArrivalBody
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ArrivalBody()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .arrival_body_profile_id import ArrivalBody_profile_id
        from .arrival_body_referrer_shape import ArrivalBody_referrer_shape
        from .arrival_body_session_id import ArrivalBody_session_id

        from .arrival_body_profile_id import ArrivalBody_profile_id
        from .arrival_body_referrer_shape import ArrivalBody_referrer_shape
        from .arrival_body_session_id import ArrivalBody_session_id

        fields: dict[str, Callable[[Any], None]] = {
            "dest_url": lambda n : setattr(self, 'dest_url', n.get_str_value()),
            "profile_id": lambda n : setattr(self, 'profile_id', n.get_object_value(ArrivalBody_profile_id)),
            "referrer_shape": lambda n : setattr(self, 'referrer_shape', n.get_enum_value(ArrivalBody_referrer_shape)),
            "session_id": lambda n : setattr(self, 'session_id', n.get_object_value(ArrivalBody_session_id)),
            "source_title": lambda n : setattr(self, 'source_title', n.get_str_value()),
            "source_url": lambda n : setattr(self, 'source_url', n.get_str_value()),
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
        writer.write_str_value("dest_url", self.dest_url)
        writer.write_object_value("profile_id", self.profile_id)
        writer.write_enum_value("referrer_shape", self.referrer_shape)
        writer.write_object_value("session_id", self.session_id)
        writer.write_str_value("source_title", self.source_title)
        writer.write_str_value("source_url", self.source_url)
        writer.write_additional_data_value(self.additional_data)
    

