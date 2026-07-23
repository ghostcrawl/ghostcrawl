from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .profile_update_request_name import ProfileUpdateRequest_name
    from .profile_update_request_storage_state_id import ProfileUpdateRequest_storage_state_id

@dataclass
class ProfileUpdateRequest(AdditionalDataHolder, Parsable):
    """
    PUT /v1/profiles/{name} body, rename and/or rebind storage_state.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # New name (rename). Unique per org.
    name: Optional[ProfileUpdateRequest_name] = None
    # Rebind storage_state id. Pass null to keep; use empty string '' to clear.
    storage_state_id: Optional[ProfileUpdateRequest_storage_state_id] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ProfileUpdateRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ProfileUpdateRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ProfileUpdateRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .profile_update_request_name import ProfileUpdateRequest_name
        from .profile_update_request_storage_state_id import ProfileUpdateRequest_storage_state_id

        from .profile_update_request_name import ProfileUpdateRequest_name
        from .profile_update_request_storage_state_id import ProfileUpdateRequest_storage_state_id

        fields: dict[str, Callable[[Any], None]] = {
            "name": lambda n : setattr(self, 'name', n.get_object_value(ProfileUpdateRequest_name)),
            "storage_state_id": lambda n : setattr(self, 'storage_state_id', n.get_object_value(ProfileUpdateRequest_storage_state_id)),
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
        writer.write_object_value("name", self.name)
        writer.write_object_value("storage_state_id", self.storage_state_id)
        writer.write_additional_data_value(self.additional_data)
    

