from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .extend_body_ttl_seconds import ExtendBody_ttl_seconds

@dataclass
class ExtendBody(AdditionalDataHolder, Parsable):
    """
    Body for POST /v1/sessions/{id}/extend.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # New TTL in seconds (30s. 24h). Omit for the store default.
    ttl_seconds: Optional[ExtendBody_ttl_seconds] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ExtendBody:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ExtendBody
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ExtendBody()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .extend_body_ttl_seconds import ExtendBody_ttl_seconds

        from .extend_body_ttl_seconds import ExtendBody_ttl_seconds

        fields: dict[str, Callable[[Any], None]] = {
            "ttl_seconds": lambda n : setattr(self, 'ttl_seconds', n.get_object_value(ExtendBody_ttl_seconds)),
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
        writer.write_object_value("ttl_seconds", self.ttl_seconds)
        writer.write_additional_data_value(self.additional_data)
    

