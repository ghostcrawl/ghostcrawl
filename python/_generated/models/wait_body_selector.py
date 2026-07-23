from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .wait_body_selector_member1 import WaitBody_selectorMember1

@dataclass
class WaitBody_selector(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes str, WaitBody_selectorMember1
    """
    # Composed type representation for type str
    string: Optional[str] = None
    # Composed type representation for type WaitBody_selectorMember1
    wait_body_selector_member1: Optional[WaitBody_selectorMember1] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> WaitBody_selector:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: WaitBody_selector
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = WaitBody_selector()
        if string_value := parse_node.get_str_value():
            result.string = string_value
        else:
            from .wait_body_selector_member1 import WaitBody_selectorMember1

            result.wait_body_selector_member1 = WaitBody_selectorMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .wait_body_selector_member1 import WaitBody_selectorMember1

        if self.wait_body_selector_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.wait_body_selector_member1)
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
            writer.write_object_value(None, self.wait_body_selector_member1)
    

