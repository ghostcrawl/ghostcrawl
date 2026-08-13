from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .extend_body_ttl_seconds_member1 import ExtendBody_ttl_secondsMember1

@dataclass
class ExtendBody_ttl_seconds(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes ExtendBody_ttl_secondsMember1, int
    """
    # Composed type representation for type ExtendBody_ttl_secondsMember1
    extend_body_ttl_seconds_member1: Optional[ExtendBody_ttl_secondsMember1] = None
    # Composed type representation for type int
    integer: Optional[int] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ExtendBody_ttl_seconds:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ExtendBody_ttl_seconds
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = ExtendBody_ttl_seconds()
        if integer_value := parse_node.get_int_value():
            result.integer = integer_value
        else:
            from .extend_body_ttl_seconds_member1 import ExtendBody_ttl_secondsMember1

            result.extend_body_ttl_seconds_member1 = ExtendBody_ttl_secondsMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .extend_body_ttl_seconds_member1 import ExtendBody_ttl_secondsMember1

        if self.extend_body_ttl_seconds_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.extend_body_ttl_seconds_member1)
        return {}
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        if self.integer:
            writer.write_int_value(None, self.integer)
        else:
            writer.write_object_value(None, self.extend_body_ttl_seconds_member1)
    

