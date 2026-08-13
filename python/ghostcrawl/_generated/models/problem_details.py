from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.api_error import APIError
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .error_code import ErrorCode

@dataclass
class ProblemDetails(APIError, AdditionalDataHolder, Parsable):
    """
    Returned on a non-2xx response when the request could not be completed on our side (authentication, rate limiting, capacity, render timeout, …). Sent with the `application/problem+json` media type (RFC 9457).
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The stable, machine-readable error code.
    code: Optional[ErrorCode] = None
    # A human-readable explanation specific to this occurrence.
    detail: Optional[str] = None
    # The request identifier for this occurrence (the same value as the `X-Request-Id` response header). Quote it when contacting support.
    instance: Optional[str] = None
    # Suggested number of seconds to wait before retrying. Present only on retryable codes; mirrors the `Retry-After` response header when set.
    retry_after: Optional[int] = None
    # Whether retrying the same call (after a short backoff) can succeed. `false` means the request will keep failing until you change something.
    retryable: Optional[bool] = None
    # The HTTP status code for this response.
    status: Optional[int] = None
    # A short, human-readable summary of the error type.
    title: Optional[str] = None
    # A stable URI that identifies the error type. Dereferences to the matching entry on the public error reference.
    type: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ProblemDetails:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ProblemDetails
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ProblemDetails()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .error_code import ErrorCode

        from .error_code import ErrorCode

        fields: dict[str, Callable[[Any], None]] = {
            "code": lambda n : setattr(self, 'code', n.get_enum_value(ErrorCode)),
            "detail": lambda n : setattr(self, 'detail', n.get_str_value()),
            "instance": lambda n : setattr(self, 'instance', n.get_str_value()),
            "retry_after": lambda n : setattr(self, 'retry_after', n.get_int_value()),
            "retryable": lambda n : setattr(self, 'retryable', n.get_bool_value()),
            "status": lambda n : setattr(self, 'status', n.get_int_value()),
            "title": lambda n : setattr(self, 'title', n.get_str_value()),
            "type": lambda n : setattr(self, 'type', n.get_str_value()),
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
        writer.write_enum_value("code", self.code)
        writer.write_str_value("detail", self.detail)
        writer.write_str_value("instance", self.instance)
        writer.write_int_value("retry_after", self.retry_after)
        writer.write_bool_value("retryable", self.retryable)
        writer.write_int_value("status", self.status)
        writer.write_str_value("title", self.title)
        writer.write_str_value("type", self.type)
        writer.write_additional_data_value(self.additional_data)
    
    @property
    def primary_message(self) -> Optional[str]:
        """
        The primary error message.
        """
        return super().message

