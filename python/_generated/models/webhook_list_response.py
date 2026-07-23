from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .webhook_list_response_next_cursor import WebhookListResponse_next_cursor
    from .webhook_public import WebhookPublic

@dataclass
class WebhookListResponse(AdditionalDataHolder, Parsable):
    """
    Response for GET /v1/webhooks (cursor-paginated list).
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The items property
    items: Optional[list[WebhookPublic]] = None
    # The next_cursor property
    next_cursor: Optional[WebhookListResponse_next_cursor] = None
    # The total property
    total: Optional[int] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> WebhookListResponse:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: WebhookListResponse
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return WebhookListResponse()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .webhook_list_response_next_cursor import WebhookListResponse_next_cursor
        from .webhook_public import WebhookPublic

        from .webhook_list_response_next_cursor import WebhookListResponse_next_cursor
        from .webhook_public import WebhookPublic

        fields: dict[str, Callable[[Any], None]] = {
            "items": lambda n : setattr(self, 'items', n.get_collection_of_object_values(WebhookPublic)),
            "next_cursor": lambda n : setattr(self, 'next_cursor', n.get_object_value(WebhookListResponse_next_cursor)),
            "total": lambda n : setattr(self, 'total', n.get_int_value()),
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
        writer.write_collection_of_object_values("items", self.items)
        writer.write_object_value("next_cursor", self.next_cursor)
        writer.write_int_value("total", self.total)
        writer.write_additional_data_value(self.additional_data)
    

