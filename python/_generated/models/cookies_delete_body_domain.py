from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .cookies_delete_body_domain_member1 import CookiesDeleteBody_domainMember1

@dataclass
class CookiesDeleteBody_domain(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes CookiesDeleteBody_domainMember1, str
    """
    # Composed type representation for type CookiesDeleteBody_domainMember1
    cookies_delete_body_domain_member1: Optional[CookiesDeleteBody_domainMember1] = None
    # Composed type representation for type str
    string: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> CookiesDeleteBody_domain:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: CookiesDeleteBody_domain
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = CookiesDeleteBody_domain()
        if string_value := parse_node.get_str_value():
            result.string = string_value
        else:
            from .cookies_delete_body_domain_member1 import CookiesDeleteBody_domainMember1

            result.cookies_delete_body_domain_member1 = CookiesDeleteBody_domainMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .cookies_delete_body_domain_member1 import CookiesDeleteBody_domainMember1

        if self.cookies_delete_body_domain_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.cookies_delete_body_domain_member1)
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
            writer.write_object_value(None, self.cookies_delete_body_domain_member1)
    

