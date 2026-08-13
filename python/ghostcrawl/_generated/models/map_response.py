from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .map_response_truncated_to_server_max import MapResponse_truncated_to_server_max

@dataclass
class MapResponse(AdditionalDataHolder, Parsable):
    """
    Response envelope for POST /v1/map.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The links property
    links: Optional[list[str]] = None
    # The success property
    success: Optional[bool] = None
    # The truncated_to_server_max property
    truncated_to_server_max: Optional[MapResponse_truncated_to_server_max] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> MapResponse:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: MapResponse
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return MapResponse()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .map_response_truncated_to_server_max import MapResponse_truncated_to_server_max

        from .map_response_truncated_to_server_max import MapResponse_truncated_to_server_max

        fields: dict[str, Callable[[Any], None]] = {
            "links": lambda n : setattr(self, 'links', n.get_collection_of_primitive_values(str)),
            "success": lambda n : setattr(self, 'success', n.get_bool_value()),
            "truncated_to_server_max": lambda n : setattr(self, 'truncated_to_server_max', n.get_object_value(MapResponse_truncated_to_server_max)),
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
        writer.write_collection_of_primitive_values("links", self.links)
        writer.write_bool_value("success", self.success)
        writer.write_object_value("truncated_to_server_max", self.truncated_to_server_max)
        writer.write_additional_data_value(self.additional_data)
    

