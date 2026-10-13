from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .cdp_input_request_button import CdpInputRequest_button
    from .cdp_input_request_step_type import CdpInputRequest_step_type
    from .cdp_input_request_text import CdpInputRequest_text
    from .cdp_input_request_url import CdpInputRequest_url
    from .cdp_input_request_wait_until import CdpInputRequest_wait_until
    from .cdp_input_request_x import CdpInputRequest_x
    from .cdp_input_request_y import CdpInputRequest_y

@dataclass
class CdpInputRequest(AdditionalDataHolder, Parsable):
    """
    POST /v1/cdp/input body. Drives a live interactive session. ``step_type`` is one of navigate/click/type: * navigate → ``url`` * click → ``x``/``y`` (CSS px) + optional ``button`` * type → ``text``
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The button property
    button: Optional[CdpInputRequest_button] = None
    # The session_id property
    session_id: Optional[str] = None
    # The step_type property
    step_type: Optional[CdpInputRequest_step_type] = None
    # The text property
    text: Optional[CdpInputRequest_text] = None
    # The url property
    url: Optional[CdpInputRequest_url] = None
    # The wait_until property
    wait_until: Optional[CdpInputRequest_wait_until] = None
    # The x property
    x: Optional[CdpInputRequest_x] = None
    # The y property
    y: Optional[CdpInputRequest_y] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> CdpInputRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: CdpInputRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return CdpInputRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .cdp_input_request_button import CdpInputRequest_button
        from .cdp_input_request_step_type import CdpInputRequest_step_type
        from .cdp_input_request_text import CdpInputRequest_text
        from .cdp_input_request_url import CdpInputRequest_url
        from .cdp_input_request_wait_until import CdpInputRequest_wait_until
        from .cdp_input_request_x import CdpInputRequest_x
        from .cdp_input_request_y import CdpInputRequest_y

        from .cdp_input_request_button import CdpInputRequest_button
        from .cdp_input_request_step_type import CdpInputRequest_step_type
        from .cdp_input_request_text import CdpInputRequest_text
        from .cdp_input_request_url import CdpInputRequest_url
        from .cdp_input_request_wait_until import CdpInputRequest_wait_until
        from .cdp_input_request_x import CdpInputRequest_x
        from .cdp_input_request_y import CdpInputRequest_y

        fields: dict[str, Callable[[Any], None]] = {
            "button": lambda n : setattr(self, 'button', n.get_object_value(CdpInputRequest_button)),
            "session_id": lambda n : setattr(self, 'session_id', n.get_str_value()),
            "step_type": lambda n : setattr(self, 'step_type', n.get_enum_value(CdpInputRequest_step_type)),
            "text": lambda n : setattr(self, 'text', n.get_object_value(CdpInputRequest_text)),
            "url": lambda n : setattr(self, 'url', n.get_object_value(CdpInputRequest_url)),
            "wait_until": lambda n : setattr(self, 'wait_until', n.get_object_value(CdpInputRequest_wait_until)),
            "x": lambda n : setattr(self, 'x', n.get_object_value(CdpInputRequest_x)),
            "y": lambda n : setattr(self, 'y', n.get_object_value(CdpInputRequest_y)),
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
        writer.write_object_value("button", self.button)
        writer.write_str_value("session_id", self.session_id)
        writer.write_enum_value("step_type", self.step_type)
        writer.write_object_value("text", self.text)
        writer.write_object_value("url", self.url)
        writer.write_object_value("wait_until", self.wait_until)
        writer.write_object_value("x", self.x)
        writer.write_object_value("y", self.y)
        writer.write_additional_data_value(self.additional_data)
    

