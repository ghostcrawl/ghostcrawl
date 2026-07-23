from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .session_create_request_engine import SessionCreateRequest_engine
    from .session_create_request_profile import SessionCreateRequest_profile

@dataclass
class SessionCreateRequest(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    from .session_create_request_engine import SessionCreateRequest_engine

    # The engine property
    engine: Optional[SessionCreateRequest_engine] = SessionCreateRequest_engine("chrome")
    # Rehydrates the saved identity bundle for this session, same deterministic fingerprint as /v1/scrape with profile=<name>.
    profile: Optional[SessionCreateRequest_profile] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> SessionCreateRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: SessionCreateRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return SessionCreateRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .session_create_request_engine import SessionCreateRequest_engine
        from .session_create_request_profile import SessionCreateRequest_profile

        from .session_create_request_engine import SessionCreateRequest_engine
        from .session_create_request_profile import SessionCreateRequest_profile

        fields: dict[str, Callable[[Any], None]] = {
            "engine": lambda n : setattr(self, 'engine', n.get_enum_value(SessionCreateRequest_engine)),
            "profile": lambda n : setattr(self, 'profile', n.get_object_value(SessionCreateRequest_profile)),
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
        writer.write_enum_value("engine", self.engine)
        writer.write_object_value("profile", self.profile)
        writer.write_additional_data_value(self.additional_data)
    

