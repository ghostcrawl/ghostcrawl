from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .scrape_request_behavior_actions_member1 import ScrapeRequest_behavior_actionsMember1
    from .scrape_request_behavior_actions_member2 import ScrapeRequest_behavior_actionsMember2

@dataclass
class ScrapeRequest_behavior_actions(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes list[ScrapeRequest_behavior_actionsMember1], ScrapeRequest_behavior_actionsMember2
    """
    # Composed type representation for type list[ScrapeRequest_behavior_actionsMember1]
    scrape_request_behavior_actions_member1: Optional[list[ScrapeRequest_behavior_actionsMember1]] = None
    # Composed type representation for type ScrapeRequest_behavior_actionsMember2
    scrape_request_behavior_actions_member2: Optional[ScrapeRequest_behavior_actionsMember2] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ScrapeRequest_behavior_actions:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ScrapeRequest_behavior_actions
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = ScrapeRequest_behavior_actions()
        if scrape_request_behavior_actions_member1_value := parse_node.get_collection_of_object_values(ScrapeRequest_behavior_actionsMember1):
            result.scrape_request_behavior_actions_member1 = scrape_request_behavior_actions_member1_value
        else:
            from .scrape_request_behavior_actions_member2 import ScrapeRequest_behavior_actionsMember2

            result.scrape_request_behavior_actions_member2 = ScrapeRequest_behavior_actionsMember2()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .scrape_request_behavior_actions_member1 import ScrapeRequest_behavior_actionsMember1
        from .scrape_request_behavior_actions_member2 import ScrapeRequest_behavior_actionsMember2

        if self.scrape_request_behavior_actions_member2:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.scrape_request_behavior_actions_member2)
        return {}
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        if self.scrape_request_behavior_actions_member1:
            writer.write_collection_of_object_values(None, self.scrape_request_behavior_actions_member1)
        else:
            writer.write_object_value(None, self.scrape_request_behavior_actions_member2)
    

