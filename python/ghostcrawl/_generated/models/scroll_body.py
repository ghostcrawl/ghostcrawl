from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .scroll_body_direction import ScrollBody_direction
    from .scroll_body_distance_px import ScrollBody_distance_px
    from .scroll_body_dy import ScrollBody_dy
    from .scroll_body_profile_id import ScrollBody_profile_id
    from .scroll_body_selector import ScrollBody_selector
    from .scroll_body_session_id import ScrollBody_session_id

@dataclass
class ScrollBody(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    from .scroll_body_direction import ScrollBody_direction

    # The direction property
    direction: Optional[ScrollBody_direction] = ScrollBody_direction("down")
    # The distance_px property
    distance_px: Optional[ScrollBody_distance_px] = None
    # The dy property
    dy: Optional[ScrollBody_dy] = None
    # The profile_id property
    profile_id: Optional[ScrollBody_profile_id] = None
    # The selector property
    selector: Optional[ScrollBody_selector] = None
    # The session_id property
    session_id: Optional[ScrollBody_session_id] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ScrollBody:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ScrollBody
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ScrollBody()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .scroll_body_direction import ScrollBody_direction
        from .scroll_body_distance_px import ScrollBody_distance_px
        from .scroll_body_dy import ScrollBody_dy
        from .scroll_body_profile_id import ScrollBody_profile_id
        from .scroll_body_selector import ScrollBody_selector
        from .scroll_body_session_id import ScrollBody_session_id

        from .scroll_body_direction import ScrollBody_direction
        from .scroll_body_distance_px import ScrollBody_distance_px
        from .scroll_body_dy import ScrollBody_dy
        from .scroll_body_profile_id import ScrollBody_profile_id
        from .scroll_body_selector import ScrollBody_selector
        from .scroll_body_session_id import ScrollBody_session_id

        fields: dict[str, Callable[[Any], None]] = {
            "direction": lambda n : setattr(self, 'direction', n.get_enum_value(ScrollBody_direction)),
            "distance_px": lambda n : setattr(self, 'distance_px', n.get_object_value(ScrollBody_distance_px)),
            "dy": lambda n : setattr(self, 'dy', n.get_object_value(ScrollBody_dy)),
            "profile_id": lambda n : setattr(self, 'profile_id', n.get_object_value(ScrollBody_profile_id)),
            "selector": lambda n : setattr(self, 'selector', n.get_object_value(ScrollBody_selector)),
            "session_id": lambda n : setattr(self, 'session_id', n.get_object_value(ScrollBody_session_id)),
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
        writer.write_enum_value("direction", self.direction)
        writer.write_object_value("distance_px", self.distance_px)
        writer.write_object_value("dy", self.dy)
        writer.write_object_value("profile_id", self.profile_id)
        writer.write_object_value("selector", self.selector)
        writer.write_object_value("session_id", self.session_id)
        writer.write_additional_data_value(self.additional_data)
    

