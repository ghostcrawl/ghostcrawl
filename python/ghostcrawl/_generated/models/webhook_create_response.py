from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .webhook_public import WebhookPublic

@dataclass
class WebhookCreateResponse(AdditionalDataHolder, Parsable):
    """
    Response for POST /v1/webhooks (201 Created). `secret` is the plaintext signing secret returned ONCE. Store it immediately, subsequent GET calls return WebhookPublic which excludes the secret.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # Plaintext signing secret. Returned only once, store it now.
    secret: Optional[str] = None
    # Public webhook subscription details. The signing secret is never included in list or get responses, it is returned only at creation time or after a secret rotation.
    webhook: Optional[WebhookPublic] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> WebhookCreateResponse:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: WebhookCreateResponse
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return WebhookCreateResponse()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .webhook_public import WebhookPublic

        from .webhook_public import WebhookPublic

        fields: dict[str, Callable[[Any], None]] = {
            "secret": lambda n : setattr(self, 'secret', n.get_str_value()),
            "webhook": lambda n : setattr(self, 'webhook', n.get_object_value(WebhookPublic)),
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
        writer.write_str_value("secret", self.secret)
        writer.write_object_value("webhook", self.webhook)
        writer.write_additional_data_value(self.additional_data)
    

