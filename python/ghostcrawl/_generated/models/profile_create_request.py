from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .profile_create_request_storage_state_id import ProfileCreateRequest_storage_state_id

@dataclass
class ProfileCreateRequest(AdditionalDataHolder, Parsable):
    """
    POST /v1/profiles body, create a named persistent profile.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # Profile name. Unique per org (409 on conflict).
    name: Optional[str] = None
    # Optional storage_state id to bind (cookies/localStorage).
    storage_state_id: Optional[ProfileCreateRequest_storage_state_id] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ProfileCreateRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ProfileCreateRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ProfileCreateRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .profile_create_request_storage_state_id import ProfileCreateRequest_storage_state_id

        from .profile_create_request_storage_state_id import ProfileCreateRequest_storage_state_id

        fields: dict[str, Callable[[Any], None]] = {
            "name": lambda n : setattr(self, 'name', n.get_str_value()),
            "storage_state_id": lambda n : setattr(self, 'storage_state_id', n.get_object_value(ProfileCreateRequest_storage_state_id)),
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
        writer.write_str_value("name", self.name)
        writer.write_object_value("storage_state_id", self.storage_state_id)
        writer.write_additional_data_value(self.additional_data)
    

