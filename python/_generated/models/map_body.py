from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .map_body_search import MapBody_search

@dataclass
class MapBody(AdditionalDataHolder, Parsable):
    """
    Firecrawl-compatible /v1/map request body. naming convention warnings for intentional camelCase).
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The ignoreSitemap property
    ignore_sitemap: Optional[bool] = False
    # The includeSubdomains property
    include_subdomains: Optional[bool] = False
    # The limit property
    limit: Optional[int] = 5000
    # The search property
    search: Optional[MapBody_search] = None
    # The url property
    url: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> MapBody:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: MapBody
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return MapBody()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .map_body_search import MapBody_search

        from .map_body_search import MapBody_search

        fields: dict[str, Callable[[Any], None]] = {
            "ignoreSitemap": lambda n : setattr(self, 'ignore_sitemap', n.get_bool_value()),
            "includeSubdomains": lambda n : setattr(self, 'include_subdomains', n.get_bool_value()),
            "limit": lambda n : setattr(self, 'limit', n.get_int_value()),
            "search": lambda n : setattr(self, 'search', n.get_object_value(MapBody_search)),
            "url": lambda n : setattr(self, 'url', n.get_str_value()),
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
        writer.write_bool_value("ignoreSitemap", self.ignore_sitemap)
        writer.write_bool_value("includeSubdomains", self.include_subdomains)
        writer.write_int_value("limit", self.limit)
        writer.write_object_value("search", self.search)
        writer.write_str_value("url", self.url)
        writer.write_additional_data_value(self.additional_data)
    

