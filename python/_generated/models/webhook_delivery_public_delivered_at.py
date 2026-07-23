from __future__ import annotations
import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .webhook_delivery_public_delivered_at_member1 import WebhookDeliveryPublic_delivered_atMember1

@dataclass
class WebhookDeliveryPublic_delivered_at(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes datetime.datetime, WebhookDeliveryPublic_delivered_atMember1
    """
    # Composed type representation for type datetime.datetime
    date_time_offset: Optional[datetime.datetime] = None
    # Composed type representation for type WebhookDeliveryPublic_delivered_atMember1
    webhook_delivery_public_delivered_at_member1: Optional[WebhookDeliveryPublic_delivered_atMember1] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> WebhookDeliveryPublic_delivered_at:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: WebhookDeliveryPublic_delivered_at
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = WebhookDeliveryPublic_delivered_at()
        if date_time_offset_value := parse_node.get_datetime_value():
            result.date_time_offset = date_time_offset_value
        else:
            from .webhook_delivery_public_delivered_at_member1 import WebhookDeliveryPublic_delivered_atMember1

            result.webhook_delivery_public_delivered_at_member1 = WebhookDeliveryPublic_delivered_atMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .webhook_delivery_public_delivered_at_member1 import WebhookDeliveryPublic_delivered_atMember1

        if self.webhook_delivery_public_delivered_at_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.webhook_delivery_public_delivered_at_member1)
        return {}
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        if self.date_time_offset:
            writer.write_datetime_value(None, self.date_time_offset)
        else:
            writer.write_object_value(None, self.webhook_delivery_public_delivered_at_member1)
    

