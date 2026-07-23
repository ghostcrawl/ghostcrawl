from __future__ import annotations
import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union
from uuid import UUID

@dataclass
class RetryDeliveryResponse(AdditionalDataHolder, Parsable):
    """
    Response for POST /v1/webhooks/{id}/deliveries/{delivery_id}/retry (202 Accepted). The original event_id is preserved so downstream consumers can detect the retry; a fresh delivery_id is assigned for the new attempt.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The enqueued_at property
    enqueued_at: Optional[datetime.datetime] = None
    # The new_delivery_id property
    new_delivery_id: Optional[UUID] = None
    # The original_delivery_id property
    original_delivery_id: Optional[UUID] = None
    # The webhook_id property
    webhook_id: Optional[UUID] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> RetryDeliveryResponse:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: RetryDeliveryResponse
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return RetryDeliveryResponse()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "enqueued_at": lambda n : setattr(self, 'enqueued_at', n.get_datetime_value()),
            "new_delivery_id": lambda n : setattr(self, 'new_delivery_id', n.get_uuid_value()),
            "original_delivery_id": lambda n : setattr(self, 'original_delivery_id', n.get_uuid_value()),
            "webhook_id": lambda n : setattr(self, 'webhook_id', n.get_uuid_value()),
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
        writer.write_datetime_value("enqueued_at", self.enqueued_at)
        writer.write_uuid_value("new_delivery_id", self.new_delivery_id)
        writer.write_uuid_value("original_delivery_id", self.original_delivery_id)
        writer.write_uuid_value("webhook_id", self.webhook_id)
        writer.write_additional_data_value(self.additional_data)
    

