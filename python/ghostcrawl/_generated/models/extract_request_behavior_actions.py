from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .extract_request_behavior_actions_member1 import ExtractRequest_behavior_actionsMember1
    from .extract_request_behavior_actions_member2 import ExtractRequest_behavior_actionsMember2

@dataclass
class ExtractRequest_behavior_actions(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes ExtractRequest_behavior_actionsMember2, list[ExtractRequest_behavior_actionsMember1]
    """
    # Composed type representation for type list[ExtractRequest_behavior_actionsMember1]
    extract_request_behavior_actions_member1: Optional[list[ExtractRequest_behavior_actionsMember1]] = None
    # Composed type representation for type ExtractRequest_behavior_actionsMember2
    extract_request_behavior_actions_member2: Optional[ExtractRequest_behavior_actionsMember2] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ExtractRequest_behavior_actions:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ExtractRequest_behavior_actions
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = ExtractRequest_behavior_actions()
        if extract_request_behavior_actions_member1_value := parse_node.get_collection_of_object_values(ExtractRequest_behavior_actionsMember1):
            result.extract_request_behavior_actions_member1 = extract_request_behavior_actions_member1_value
        else:
            from .extract_request_behavior_actions_member2 import ExtractRequest_behavior_actionsMember2

            result.extract_request_behavior_actions_member2 = ExtractRequest_behavior_actionsMember2()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .extract_request_behavior_actions_member1 import ExtractRequest_behavior_actionsMember1
        from .extract_request_behavior_actions_member2 import ExtractRequest_behavior_actionsMember2

        if self.extract_request_behavior_actions_member2:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.extract_request_behavior_actions_member2)
        return {}
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        if self.extract_request_behavior_actions_member1:
            writer.write_collection_of_object_values(None, self.extract_request_behavior_actions_member1)
        else:
            writer.write_object_value(None, self.extract_request_behavior_actions_member2)
    

