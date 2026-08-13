from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.api_error import APIError
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union
from uuid import UUID

if TYPE_CHECKING:
    from .error_envelope_limits import ErrorEnvelope_limits

@dataclass
class ErrorEnvelope(APIError, AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The detail property
    detail: Optional[str] = None
    # The error property
    error: Optional[str] = None
    # The field property
    field: Optional[str] = None
    # The lane property
    lane: Optional[str] = None
    # The limits property
    limits: Optional[ErrorEnvelope_limits] = None
    # The ok property
    ok: Optional[bool] = None
    # The reason property
    reason: Optional[str] = None
    # The route property
    route: Optional[str] = None
    # The session_id property
    session_id: Optional[UUID] = None
    # The status property
    status: Optional[int] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ErrorEnvelope:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ErrorEnvelope
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ErrorEnvelope()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .error_envelope_limits import ErrorEnvelope_limits

        from .error_envelope_limits import ErrorEnvelope_limits

        fields: dict[str, Callable[[Any], None]] = {
            "detail": lambda n : setattr(self, 'detail', n.get_str_value()),
            "error": lambda n : setattr(self, 'error', n.get_str_value()),
            "field": lambda n : setattr(self, 'field', n.get_str_value()),
            "lane": lambda n : setattr(self, 'lane', n.get_str_value()),
            "limits": lambda n : setattr(self, 'limits', n.get_object_value(ErrorEnvelope_limits)),
            "ok": lambda n : setattr(self, 'ok', n.get_bool_value()),
            "reason": lambda n : setattr(self, 'reason', n.get_str_value()),
            "route": lambda n : setattr(self, 'route', n.get_str_value()),
            "session_id": lambda n : setattr(self, 'session_id', n.get_uuid_value()),
            "status": lambda n : setattr(self, 'status', n.get_int_value()),
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
        writer.write_str_value("detail", self.detail)
        writer.write_str_value("error", self.error)
        writer.write_str_value("field", self.field)
        writer.write_str_value("lane", self.lane)
        writer.write_object_value("limits", self.limits)
        writer.write_bool_value("ok", self.ok)
        writer.write_str_value("reason", self.reason)
        writer.write_str_value("route", self.route)
        writer.write_uuid_value("session_id", self.session_id)
        writer.write_int_value("status", self.status)
        writer.write_additional_data_value(self.additional_data)
    
    @property
    def primary_message(self) -> Optional[str]:
        """
        The primary error message.
        """
        return super().message

