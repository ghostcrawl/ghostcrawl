from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class WebhookCreateRequest(AdditionalDataHolder, Parsable):
    """
    Request body for POST /v1/webhooks.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # Allow private/internal IP targets (hosted mode only).
    allow_private_targets: Optional[bool] = False
    # Event types to subscribe to. Must be non-empty subset of: ['agent.run.completed', 'agent.run.failed', 'budget.exceeded', 'budget.warning', 'cost.daily.threshold_critical', 'cost.daily.threshold_warning', 'cost.month_end.projected_overrun', 'crawl.completed', 'dataset.updated', 'extract.completed', 'extract.failed', 'manual_test', 'recording.saved', 'scrape.completed', 'scrape.failed', 'session.ended', 'team.api_key.created', 'team.api_key.revoked', 'team.signup.verified'].
    event_types: Optional[list[str]] = None
    # Destination URL for webhook delivery. Must be HTTPS.
    url: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> WebhookCreateRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: WebhookCreateRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return WebhookCreateRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "allow_private_targets": lambda n : setattr(self, 'allow_private_targets', n.get_bool_value()),
            "event_types": lambda n : setattr(self, 'event_types', n.get_collection_of_primitive_values(str)),
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
        writer.write_bool_value("allow_private_targets", self.allow_private_targets)
        writer.write_collection_of_primitive_values("event_types", self.event_types)
        writer.write_str_value("url", self.url)
        writer.write_additional_data_value(self.additional_data)
    

