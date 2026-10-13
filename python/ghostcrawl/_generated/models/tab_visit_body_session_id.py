from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .tab_visit_body_session_id_member1 import TabVisitBody_session_idMember1

@dataclass
class TabVisitBody_session_id(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes str, TabVisitBody_session_idMember1
    """
    # Composed type representation for type str
    string: Optional[str] = None
    # Composed type representation for type TabVisitBody_session_idMember1
    tab_visit_body_session_id_member1: Optional[TabVisitBody_session_idMember1] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> TabVisitBody_session_id:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: TabVisitBody_session_id
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = TabVisitBody_session_id()
        if string_value := parse_node.get_str_value():
            result.string = string_value
        else:
            from .tab_visit_body_session_id_member1 import TabVisitBody_session_idMember1

            result.tab_visit_body_session_id_member1 = TabVisitBody_session_idMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .tab_visit_body_session_id_member1 import TabVisitBody_session_idMember1

        if self.tab_visit_body_session_id_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.tab_visit_body_session_id_member1)
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
            writer.write_object_value(None, self.tab_visit_body_session_id_member1)
    

