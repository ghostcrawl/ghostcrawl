from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class ErrorEnvelope_limits(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The active property
    active: Optional[int] = None
    # The max_active property
    max_active: Optional[int] = None
    # The max_queue property
    max_queue: Optional[int] = None
    # The queued property
    queued: Optional[int] = None
    # The reason property
    reason: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ErrorEnvelope_limits:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ErrorEnvelope_limits
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ErrorEnvelope_limits()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "active": lambda n : setattr(self, 'active', n.get_int_value()),
            "max_active": lambda n : setattr(self, 'max_active', n.get_int_value()),
            "max_queue": lambda n : setattr(self, 'max_queue', n.get_int_value()),
            "queued": lambda n : setattr(self, 'queued', n.get_int_value()),
            "reason": lambda n : setattr(self, 'reason', n.get_str_value()),
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
        writer.write_int_value("active", self.active)
        writer.write_int_value("max_active", self.max_active)
        writer.write_int_value("max_queue", self.max_queue)
        writer.write_int_value("queued", self.queued)
        writer.write_str_value("reason", self.reason)
        writer.write_additional_data_value(self.additional_data)
    

