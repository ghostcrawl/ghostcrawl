from __future__ import annotations
import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union
from uuid import UUID

if TYPE_CHECKING:
    from .webhook_delivery_public_delivered_at import WebhookDeliveryPublic_delivered_at
    from .webhook_delivery_public_error_class import WebhookDeliveryPublic_error_class
    from .webhook_delivery_public_replay_of import WebhookDeliveryPublic_replay_of
    from .webhook_delivery_public_response_body_preview import WebhookDeliveryPublic_response_body_preview
    from .webhook_delivery_public_response_status import WebhookDeliveryPublic_response_status

@dataclass
class WebhookDeliveryPublic(AdditionalDataHolder, Parsable):
    """
    Wire-public delivery log representation. 13 wire-public fields per webhook_deliveries schema. All fields are operator/integrator-facing, no secret material.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The attempt property
    attempt: Optional[int] = None
    # The delivered_at property
    delivered_at: Optional[WebhookDeliveryPublic_delivered_at] = None
    # The enqueued_at property
    enqueued_at: Optional[datetime.datetime] = None
    # The error_class property
    error_class: Optional[WebhookDeliveryPublic_error_class] = None
    # The event_id property
    event_id: Optional[UUID] = None
    # The event_type property
    event_type: Optional[str] = None
    # The id property
    id: Optional[UUID] = None
    # The org_id property
    org_id: Optional[UUID] = None
    # The replay_of property
    replay_of: Optional[WebhookDeliveryPublic_replay_of] = None
    # The response_body_preview property
    response_body_preview: Optional[WebhookDeliveryPublic_response_body_preview] = None
    # The response_status property
    response_status: Optional[WebhookDeliveryPublic_response_status] = None
    # The status property
    status: Optional[str] = None
    # The webhook_id property
    webhook_id: Optional[UUID] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> WebhookDeliveryPublic:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: WebhookDeliveryPublic
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return WebhookDeliveryPublic()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .webhook_delivery_public_delivered_at import WebhookDeliveryPublic_delivered_at
        from .webhook_delivery_public_error_class import WebhookDeliveryPublic_error_class
        from .webhook_delivery_public_replay_of import WebhookDeliveryPublic_replay_of
        from .webhook_delivery_public_response_body_preview import WebhookDeliveryPublic_response_body_preview
        from .webhook_delivery_public_response_status import WebhookDeliveryPublic_response_status

        from .webhook_delivery_public_delivered_at import WebhookDeliveryPublic_delivered_at
        from .webhook_delivery_public_error_class import WebhookDeliveryPublic_error_class
        from .webhook_delivery_public_replay_of import WebhookDeliveryPublic_replay_of
        from .webhook_delivery_public_response_body_preview import WebhookDeliveryPublic_response_body_preview
        from .webhook_delivery_public_response_status import WebhookDeliveryPublic_response_status

        fields: dict[str, Callable[[Any], None]] = {
            "attempt": lambda n : setattr(self, 'attempt', n.get_int_value()),
            "delivered_at": lambda n : setattr(self, 'delivered_at', n.get_object_value(WebhookDeliveryPublic_delivered_at)),
            "enqueued_at": lambda n : setattr(self, 'enqueued_at', n.get_datetime_value()),
            "error_class": lambda n : setattr(self, 'error_class', n.get_object_value(WebhookDeliveryPublic_error_class)),
            "event_id": lambda n : setattr(self, 'event_id', n.get_uuid_value()),
            "event_type": lambda n : setattr(self, 'event_type', n.get_str_value()),
            "id": lambda n : setattr(self, 'id', n.get_uuid_value()),
            "org_id": lambda n : setattr(self, 'org_id', n.get_uuid_value()),
            "replay_of": lambda n : setattr(self, 'replay_of', n.get_object_value(WebhookDeliveryPublic_replay_of)),
            "response_body_preview": lambda n : setattr(self, 'response_body_preview', n.get_object_value(WebhookDeliveryPublic_response_body_preview)),
            "response_status": lambda n : setattr(self, 'response_status', n.get_object_value(WebhookDeliveryPublic_response_status)),
            "status": lambda n : setattr(self, 'status', n.get_str_value()),
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
        writer.write_int_value("attempt", self.attempt)
        writer.write_object_value("delivered_at", self.delivered_at)
        writer.write_datetime_value("enqueued_at", self.enqueued_at)
        writer.write_object_value("error_class", self.error_class)
        writer.write_uuid_value("event_id", self.event_id)
        writer.write_str_value("event_type", self.event_type)
        writer.write_uuid_value("id", self.id)
        writer.write_uuid_value("org_id", self.org_id)
        writer.write_object_value("replay_of", self.replay_of)
        writer.write_object_value("response_body_preview", self.response_body_preview)
        writer.write_object_value("response_status", self.response_status)
        writer.write_str_value("status", self.status)
        writer.write_uuid_value("webhook_id", self.webhook_id)
        writer.write_additional_data_value(self.additional_data)
    

