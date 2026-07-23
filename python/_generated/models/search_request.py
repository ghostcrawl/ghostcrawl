from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .search_request_country import SearchRequest_country
    from .search_request_engine import SearchRequest_engine
    from .search_request_freshness import SearchRequest_freshness
    from .search_request_vertical import SearchRequest_vertical

@dataclass
class SearchRequest(AdditionalDataHolder, Parsable):
    """
    POST /v1/search request body.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # Maximum results (1-20).
    limit: Optional[int] = 10
    # Optional 2-letter ISO country code for geo-filter. Tavily v1 ignores this silently.
    country: Optional[SearchRequest_country] = None
    # Search engine to use: 'brave', 'tavily', 'google', 'bing', or 'yandex'. May also be passed via X-GhostCrawl-Search-Engine header.
    engine: Optional[SearchRequest_engine] = None
    # Optional freshness filter (adapter-specific; Brave: 'pd'/'pw'/'pm'/'py' for day/week/month/year).
    freshness: Optional[SearchRequest_freshness] = None
    # Search query string.
    query: Optional[str] = None
    # Engine-specific vertical (google only): 'search' (default) | 'jobs' | 'scholar' | 'play' | 'reviews'. Ignored by brave/tavily.
    vertical: Optional[SearchRequest_vertical] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> SearchRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: SearchRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return SearchRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .search_request_country import SearchRequest_country
        from .search_request_engine import SearchRequest_engine
        from .search_request_freshness import SearchRequest_freshness
        from .search_request_vertical import SearchRequest_vertical

        from .search_request_country import SearchRequest_country
        from .search_request_engine import SearchRequest_engine
        from .search_request_freshness import SearchRequest_freshness
        from .search_request_vertical import SearchRequest_vertical

        fields: dict[str, Callable[[Any], None]] = {
            "country": lambda n : setattr(self, 'country', n.get_object_value(SearchRequest_country)),
            "engine": lambda n : setattr(self, 'engine', n.get_object_value(SearchRequest_engine)),
            "freshness": lambda n : setattr(self, 'freshness', n.get_object_value(SearchRequest_freshness)),
            "limit": lambda n : setattr(self, 'limit', n.get_int_value()),
            "query": lambda n : setattr(self, 'query', n.get_str_value()),
            "vertical": lambda n : setattr(self, 'vertical', n.get_object_value(SearchRequest_vertical)),
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
        writer.write_object_value("country", self.country)
        writer.write_object_value("engine", self.engine)
        writer.write_object_value("freshness", self.freshness)
        writer.write_int_value("limit", self.limit)
        writer.write_str_value("query", self.query)
        writer.write_object_value("vertical", self.vertical)
        writer.write_additional_data_value(self.additional_data)
    

