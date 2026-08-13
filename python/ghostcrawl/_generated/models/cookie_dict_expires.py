from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .cookie_dict_expires_member1 import CookieDict_expiresMember1

@dataclass
class CookieDict_expires(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes CookieDict_expiresMember1, float
    """
    # Composed type representation for type CookieDict_expiresMember1
    cookie_dict_expires_member1: Optional[CookieDict_expiresMember1] = None
    # Composed type representation for type float
    double: Optional[float] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> CookieDict_expires:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: CookieDict_expires
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = CookieDict_expires()
        if double_value := parse_node.get_float_value():
            result.double = double_value
        else:
            from .cookie_dict_expires_member1 import CookieDict_expiresMember1

            result.cookie_dict_expires_member1 = CookieDict_expiresMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .cookie_dict_expires_member1 import CookieDict_expiresMember1

        if self.cookie_dict_expires_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.cookie_dict_expires_member1)
        return {}
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        if self.double:
            writer.write_float_value(None, self.double)
        else:
            writer.write_object_value(None, self.cookie_dict_expires_member1)
    

