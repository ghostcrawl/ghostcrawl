from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .deep_crawl_body_routing_mode import DeepCrawlBody_routing_mode
    from .deep_crawl_body_timeout_s import DeepCrawlBody_timeout_s
    from .deep_crawl_body_wait_until import DeepCrawlBody_wait_until
    from .deep_crawl_body_webhook_url import DeepCrawlBody_webhook_url
    from .filter_spec import FilterSpec
    from .scorer_spec import ScorerSpec

@dataclass
class DeepCrawlBody(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The include_sitemaps property
    include_sitemaps: Optional[bool] = False
    # The max_depth property
    max_depth: Optional[int] = 3
    # The max_urls property
    max_urls: Optional[int] = 1000
    # The respect_robots property
    respect_robots: Optional[bool] = True
    from .deep_crawl_body_routing_mode import DeepCrawlBody_routing_mode

    # Routing mode. auto (default) = we pick the cheapest network that succeeds and automatically escalate on a block. standard = normal targets only. premium = always use our premium network. Most callers should leave this at auto.
    routing_mode: Optional[DeepCrawlBody_routing_mode] = DeepCrawlBody_routing_mode("auto")
    # The strategy property
    strategy: Optional[str] = "bfs"
    # The stream property
    stream: Optional[bool] = False
    # The filters property
    filters: Optional[list[FilterSpec]] = None
    # The scorer property
    scorer: Optional[ScorerSpec] = None
    # The seed_urls property
    seed_urls: Optional[list[str]] = None
    # The timeout_s property
    timeout_s: Optional[DeepCrawlBody_timeout_s] = None
    # The wait_until property
    wait_until: Optional[DeepCrawlBody_wait_until] = None
    # The webhook_url property
    webhook_url: Optional[DeepCrawlBody_webhook_url] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> DeepCrawlBody:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: DeepCrawlBody
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return DeepCrawlBody()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .deep_crawl_body_routing_mode import DeepCrawlBody_routing_mode
        from .deep_crawl_body_timeout_s import DeepCrawlBody_timeout_s
        from .deep_crawl_body_wait_until import DeepCrawlBody_wait_until
        from .deep_crawl_body_webhook_url import DeepCrawlBody_webhook_url
        from .filter_spec import FilterSpec
        from .scorer_spec import ScorerSpec

        from .deep_crawl_body_routing_mode import DeepCrawlBody_routing_mode
        from .deep_crawl_body_timeout_s import DeepCrawlBody_timeout_s
        from .deep_crawl_body_wait_until import DeepCrawlBody_wait_until
        from .deep_crawl_body_webhook_url import DeepCrawlBody_webhook_url
        from .filter_spec import FilterSpec
        from .scorer_spec import ScorerSpec

        fields: dict[str, Callable[[Any], None]] = {
            "filters": lambda n : setattr(self, 'filters', n.get_collection_of_object_values(FilterSpec)),
            "include_sitemaps": lambda n : setattr(self, 'include_sitemaps', n.get_bool_value()),
            "max_depth": lambda n : setattr(self, 'max_depth', n.get_int_value()),
            "max_urls": lambda n : setattr(self, 'max_urls', n.get_int_value()),
            "respect_robots": lambda n : setattr(self, 'respect_robots', n.get_bool_value()),
            "routing_mode": lambda n : setattr(self, 'routing_mode', n.get_enum_value(DeepCrawlBody_routing_mode)),
            "scorer": lambda n : setattr(self, 'scorer', n.get_object_value(ScorerSpec)),
            "seed_urls": lambda n : setattr(self, 'seed_urls', n.get_collection_of_primitive_values(str)),
            "strategy": lambda n : setattr(self, 'strategy', n.get_str_value()),
            "stream": lambda n : setattr(self, 'stream', n.get_bool_value()),
            "timeout_s": lambda n : setattr(self, 'timeout_s', n.get_object_value(DeepCrawlBody_timeout_s)),
            "wait_until": lambda n : setattr(self, 'wait_until', n.get_object_value(DeepCrawlBody_wait_until)),
            "webhook_url": lambda n : setattr(self, 'webhook_url', n.get_object_value(DeepCrawlBody_webhook_url)),
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
        writer.write_collection_of_object_values("filters", self.filters)
        writer.write_bool_value("include_sitemaps", self.include_sitemaps)
        writer.write_int_value("max_depth", self.max_depth)
        writer.write_int_value("max_urls", self.max_urls)
        writer.write_bool_value("respect_robots", self.respect_robots)
        writer.write_enum_value("routing_mode", self.routing_mode)
        writer.write_object_value("scorer", self.scorer)
        writer.write_collection_of_primitive_values("seed_urls", self.seed_urls)
        writer.write_str_value("strategy", self.strategy)
        writer.write_bool_value("stream", self.stream)
        writer.write_object_value("timeout_s", self.timeout_s)
        writer.write_object_value("wait_until", self.wait_until)
        writer.write_object_value("webhook_url", self.webhook_url)
        writer.write_additional_data_value(self.additional_data)
    

