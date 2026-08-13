from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import ComposedTypeWrapper, Parsable, ParseNode, ParseNodeHelper, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .scrape_result_token_estimate_member1 import ScrapeResult_token_estimateMember1

@dataclass
class ScrapeResult_token_estimate(ComposedTypeWrapper, Parsable):
    """
    Composed type wrapper for classes int, ScrapeResult_token_estimateMember1
    """
    # Composed type representation for type int
    integer: Optional[int] = None
    # Composed type representation for type ScrapeResult_token_estimateMember1
    scrape_result_token_estimate_member1: Optional[ScrapeResult_token_estimateMember1] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ScrapeResult_token_estimate:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ScrapeResult_token_estimate
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        result = ScrapeResult_token_estimate()
        if integer_value := parse_node.get_int_value():
            result.integer = integer_value
        else:
            from .scrape_result_token_estimate_member1 import ScrapeResult_token_estimateMember1

            result.scrape_result_token_estimate_member1 = ScrapeResult_token_estimateMember1()
        return result
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .scrape_result_token_estimate_member1 import ScrapeResult_token_estimateMember1

        if self.scrape_result_token_estimate_member1:
            return ParseNodeHelper.merge_deserializers_for_intersection_wrapper(self.scrape_result_token_estimate_member1)
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
            writer.write_object_value(None, self.scrape_result_token_estimate_member1)
    

