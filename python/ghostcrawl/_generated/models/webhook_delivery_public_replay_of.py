from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union
from uuid import UUID

if TYPE_CHECKING:
    from .webhook_delivery_public_replay_of_member1 import WebhookDeliveryPublic_replay_ofMember1

@dataclass
class WebhookDeliveryPublic_replay_of(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes UUID, WebhookDeliveryPublic_replay_ofMember1
    """
    # Composed type representation for type UUID
    guid: Optional[UUID] = None
    # Composed type representation for type WebhookDeliveryPublic_replay_ofMember1
    webhook_delivery_public_replay_of_member1: Optional[WebhookDeliveryPublic_replay_ofMember1] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> WebhookDeliveryPublic_replay_of:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: WebhookDeliveryPublic_replay_of
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = WebhookDeliveryPublic_replay_of()
        if guid_value := parse_node.get_uuid_value():
            result.guid = guid_value
        else:
            from .webhook_delivery_public_replay_of_member1 import WebhookDeliveryPublic_replay_ofMember1

            result.webhook_delivery_public_replay_of_member1 = WebhookDeliveryPublic_replay_ofMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .webhook_delivery_public_replay_of_member1 import WebhookDeliveryPublic_replay_ofMember1

        if self.webhook_delivery_public_replay_of_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.webhook_delivery_public_replay_of_member1)
        return {}
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        if self.guid:
            writer.write_uuid_value(None, self.guid)
        else:
            writer.write_object_value(None, self.webhook_delivery_public_replay_of_member1)
    

