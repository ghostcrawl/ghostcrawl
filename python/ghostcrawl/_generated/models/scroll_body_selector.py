from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .scroll_body_selector_member1 import ScrollBody_selectorMember1

@dataclass
class ScrollBody_selector(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes ScrollBody_selectorMember1, str
    """
    # Composed type representation for type ScrollBody_selectorMember1
    scroll_body_selector_member1: Optional[ScrollBody_selectorMember1] = None
    # Composed type representation for type str
    string: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ScrollBody_selector:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ScrollBody_selector
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = ScrollBody_selector()
        if string_value := parse_node.get_str_value():
            result.string = string_value
        else:
            from .scroll_body_selector_member1 import ScrollBody_selectorMember1

            result.scroll_body_selector_member1 = ScrollBody_selectorMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .scroll_body_selector_member1 import ScrollBody_selectorMember1

        if self.scroll_body_selector_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.scroll_body_selector_member1)
        return {}
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        if self.string:
            writer.write_str_value(None, self.string)
        else:
            writer.write_object_value(None, self.scroll_body_selector_member1)
    

