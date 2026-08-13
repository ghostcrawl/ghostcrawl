from __future__ import annotations
import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union
from uuid import UUID

if TYPE_CHECKING:
    from .webhook_public_secret_rotated_at import WebhookPublic_secret_rotated_at

@dataclass
class WebhookPublic(AdditionalDataHolder, Parsable):
    """
    Public webhook subscription details. The signing secret is never included in list or get responses, it is returned only at creation time or after a secret rotation.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The active property
    active: Optional[bool] = None
    # The allow_private_targets property
    allow_private_targets: Optional[bool] = None
    # The created_at property
    created_at: Optional[datetime.datetime] = None
    # The event_types property
    event_types: Optional[list[str]] = None
    # The id property
    id: Optional[UUID] = None
    # The org_id property
    org_id: Optional[UUID] = None
    # The owner_user_id property
    owner_user_id: Optional[UUID] = None
    # The secret_rotated_at property
    secret_rotated_at: Optional[WebhookPublic_secret_rotated_at] = None
    # The url property
    url: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> WebhookPublic:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: WebhookPublic
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return WebhookPublic()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .webhook_public_secret_rotated_at import WebhookPublic_secret_rotated_at

        from .webhook_public_secret_rotated_at import WebhookPublic_secret_rotated_at

        fields: dict[str, Callable[[Any], None]] = {
            "active": lambda n : setattr(self, 'active', n.get_bool_value()),
            "allow_private_targets": lambda n : setattr(self, 'allow_private_targets', n.get_bool_value()),
            "created_at": lambda n : setattr(self, 'created_at', n.get_datetime_value()),
            "event_types": lambda n : setattr(self, 'event_types', n.get_collection_of_primitive_values(str)),
            "id": lambda n : setattr(self, 'id', n.get_uuid_value()),
            "org_id": lambda n : setattr(self, 'org_id', n.get_uuid_value()),
            "owner_user_id": lambda n : setattr(self, 'owner_user_id', n.get_uuid_value()),
            "secret_rotated_at": lambda n : setattr(self, 'secret_rotated_at', n.get_object_value(WebhookPublic_secret_rotated_at)),
            "url": lambda n : setattr(self, 'url', n.get_str_value()),
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
        writer.write_bool_value("active", self.active)
        writer.write_bool_value("allow_private_targets", self.allow_private_targets)
        writer.write_datetime_value("created_at", self.created_at)
        writer.write_collection_of_primitive_values("event_types", self.event_types)
        writer.write_uuid_value("id", self.id)
        writer.write_uuid_value("org_id", self.org_id)
        writer.write_uuid_value("owner_user_id", self.owner_user_id)
        writer.write_object_value("secret_rotated_at", self.secret_rotated_at)
        writer.write_str_value("url", self.url)
        writer.write_additional_data_value(self.additional_data)
    

