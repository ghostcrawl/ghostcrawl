from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .ghostcrawl__api__routes__profiles__profile_update_request_269385a9 import Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_269385a9
    from .ghostcrawl__api__routes__profiles__profile_update_request_name import Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_name

@dataclass
class Ghostcrawl__api__routes__profiles__ProfileUpdateRequest(AdditionalDataHolder, Parsable):
    """
    PUT /v1/profiles/{name} body, rename and/or rebind storage_state.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # New name (rename). Unique per org.
    name: Optional[Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_name] = None
    # Rebind storage_state id. Pass null to keep; use empty string '' to clear.
    storage_state_id: Optional[Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_269385a9] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> Ghostcrawl__api__routes__profiles__ProfileUpdateRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: Ghostcrawl__api__routes__profiles__ProfileUpdateRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return Ghostcrawl__api__routes__profiles__ProfileUpdateRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .ghostcrawl__api__routes__profiles__profile_update_request_269385a9 import Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_269385a9
        from .ghostcrawl__api__routes__profiles__profile_update_request_name import Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_name

        from .ghostcrawl__api__routes__profiles__profile_update_request_269385a9 import Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_269385a9
        from .ghostcrawl__api__routes__profiles__profile_update_request_name import Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_name

        fields: dict[str, Callable[[Any], None]] = {
            "name": lambda n : setattr(self, 'name', n.get_object_value(Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_name)),
            "storage_state_id": lambda n : setattr(self, 'storage_state_id', n.get_object_value(Ghostcrawl__api__routes__profiles__ProfileUpdateRequest_269385a9)),
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
    

