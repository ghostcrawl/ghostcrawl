from __future__ import annotations
import datetime
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union
from uuid import UUID

@dataclass
class RotateSecretResponse(AdditionalDataHolder, Parsable):
    """
    Response for POST /v1/webhooks/{id}/rotate-secret. `secret` is the new signing secret. The previous secret remains valid for a short grace period so in-flight deliveries can still be verified. `prev_secret_expires_at` is when the grace period ends.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # When the previous signing secret expires and the grace period ends.
    prev_secret_expires_at: Optional[datetime.datetime] = None
    # The rotated_at property
    rotated_at: Optional[datetime.datetime] = None
    # New signing secret. The previous secret remains valid during the grace period.
    secret: Optional[str] = None
    # The webhook_id property
    webhook_id: Optional[UUID] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> RotateSecretResponse:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: RotateSecretResponse
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return RotateSecretResponse()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "prev_secret_expires_at": lambda n : setattr(self, 'prev_secret_expires_at', n.get_datetime_value()),
            "rotated_at": lambda n : setattr(self, 'rotated_at', n.get_datetime_value()),
            "secret": lambda n : setattr(self, 'secret', n.get_str_value()),
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
        writer.write_datetime_value("prev_secret_expires_at", self.prev_secret_expires_at)
        writer.write_datetime_value("rotated_at", self.rotated_at)
        writer.write_str_value("secret", self.secret)
        writer.write_uuid_value("webhook_id", self.webhook_id)
        writer.write_additional_data_value(self.additional_data)
    

