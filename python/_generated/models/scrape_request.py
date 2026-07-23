from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .scrape_request_batch_identity_mode import ScrapeRequest_batch_identity_mode
    from .scrape_request_behavior_actions import ScrapeRequest_behavior_actions
    from .scrape_request_engine import ScrapeRequest_engine
    from .scrape_request_format import ScrapeRequest_format
    from .scrape_request_identity import ScrapeRequest_identity
    from .scrape_request_identity_country import ScrapeRequest_identity_country
    from .scrape_request_language import ScrapeRequest_language
    from .scrape_request_profile import ScrapeRequest_profile
    from .scrape_request_proxy import ScrapeRequest_proxy
    from .scrape_request_routing_mode import ScrapeRequest_routing_mode
    from .scrape_request_screenshot_selector import ScrapeRequest_screenshot_selector
    from .scrape_request_session import ScrapeRequest_session
    from .scrape_request_timeout_ms import ScrapeRequest_timeout_ms
    from .scrape_request_url import ScrapeRequest_url
    from .scrape_request_urls import ScrapeRequest_urls

@dataclass
class ScrapeRequest(AdditionalDataHolder, Parsable):
    """
    POST /v1/scrape request body (-03 identity-aware shape).
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    from .scrape_request_batch_identity_mode import ScrapeRequest_batch_identity_mode

    # "persist" (default): same identity for all URLs in a batch. "randomize": fresh identity per URL (each counts against quota).
    batch_identity_mode: Optional[ScrapeRequest_batch_identity_mode] = ScrapeRequest_batch_identity_mode("persist")
    # Maximum tokens per markdown chunk. Clamped server-side to [256, 32768] regardless of caller input.
    chunk_tokens: Optional[int] = 8192
    from .scrape_request_engine import ScrapeRequest_engine

    # Engine override. 'auto' (default): the identity's fingerprint decides the engine. 'chrome'|'firefox'|'webkit': force that engine, enforced only if coherent with the identity (e.g. iOS identities are always webkit); incoherent picks are rejected, never coerced to a hybrid.
    engine: Optional[ScrapeRequest_engine] = ScrapeRequest_engine("auto")
    from .scrape_request_format import ScrapeRequest_format

    # Response format. 'html' (default): the fully rendered DOM. 'markdown': returns a {markdown, chunks, citations, token_estimate} envelope with prompt-injection-neutralized, token-budgeted output. 'pdf': returns application/pdf bytes (Chrome identities only; Firefox and WebKit return 400 pdf_engine_unsupported).
    format: Optional[ScrapeRequest_format] = ScrapeRequest_format("html")
    # When screenshot=true, capture the FULL document height instead of just the visible viewport. Ignored when screenshot_selector is set.
    full_page: Optional[bool] = False
    # When format=markdown, include deduplicated citation list {url, anchor_text} from the scraped page.
    include_citations: Optional[bool] = True
    from .scrape_request_routing_mode import ScrapeRequest_routing_mode

    # Routing mode. auto (default) = we pick the cheapest network that succeeds and automatically escalate on a block. standard = normal targets only. premium = always use our premium network. Most callers should leave this at auto.
    routing_mode: Optional[ScrapeRequest_routing_mode] = ScrapeRequest_routing_mode("auto")
    # When true, a screenshot is captured during the fetch and returned as a base64-encoded PNG in result['screenshot']. Off by default.
    screenshot: Optional[bool] = False
    # When true, returns text/event-stream with one SSE event per chunk. Per-tenant concurrency is capped (default 5). Final 'done' event carries estimated_llm_input_tokens.
    stream: Optional[bool] = False
    # BYO behavior: a list of trusted-input actions replayed on the loaded page instead of the built-in human session. Each item is {"kind":"move","x":int,"y":int} | {"kind":"wheel","x":int,"y":int,"dy":int} | {"kind":"dwell","ms":int}. Sanitized + bounded server-side (max 256 actions). Available on every tier.
    behavior_actions: Optional[ScrapeRequest_behavior_actions] = None
    # Previously-persisted identity_id from POST /v1/identity (persist=true).
    identity: Optional[ScrapeRequest_identity] = None
    # Optional two-letter country code (e.g. 'US','DE'). When set, the exit is geo-filtered to that country and the identity's timezone is derived from it. When omitted, the timezone follows the rotating exit country. Language is independent, see the `language` field.
    identity_country: Optional[ScrapeRequest_identity_country] = None
    # Optional browser language tag (e.g. 'en-US','es-ES','de-DE'). Sets the identity's locale and language headers coherently, independent of the exit country. When omitted, the identity's default locale is used. Available on every tier.
    language: Optional[ScrapeRequest_language] = None
    # Named persistent profile (multi-accounting). Resolves to a durable identity_id (→ same deterministic fingerprint) + optional saved storage_state (→ cookies/localStorage) for the calling org. Reuses the exact identity+cookies on every request, with no 30-minute sticky-session expiry. 404 if the named profile does not exist for the org.
    profile: Optional[ScrapeRequest_profile] = None
    # Bring-your-own proxy URL. Schemes: socks5, socks5h, http, https. Any credentials in the URL are redacted from logs. Example: socks5://user:pass@host:1080.
    proxy: Optional[ScrapeRequest_proxy] = None
    # When screenshot=true, clip the capture to the first DOM element matching this CSS selector (element screenshot). Takes precedence over full_page.
    screenshot_selector: Optional[ScrapeRequest_screenshot_selector] = None
    # Sticky-session token (paid tiers). Requests sharing a token reuse the same identity → same exit + cookies (returning-visitor coherence). Bounded TTL; opaque [A-Za-z0-9._-], max 128 chars.
    session: Optional[ScrapeRequest_session] = None
    # Optional per-request timeout in milliseconds. Clamped server-side to ≤120000 ms (120s); values outside [0, 120000] are rejected (422).
    timeout_ms: Optional[ScrapeRequest_timeout_ms] = None
    # The url property
    url: Optional[ScrapeRequest_url] = None
    # The urls property
    urls: Optional[ScrapeRequest_urls] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ScrapeRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ScrapeRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ScrapeRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .scrape_request_batch_identity_mode import ScrapeRequest_batch_identity_mode
        from .scrape_request_behavior_actions import ScrapeRequest_behavior_actions
        from .scrape_request_engine import ScrapeRequest_engine
        from .scrape_request_format import ScrapeRequest_format
        from .scrape_request_identity import ScrapeRequest_identity
        from .scrape_request_identity_country import ScrapeRequest_identity_country
        from .scrape_request_language import ScrapeRequest_language
        from .scrape_request_profile import ScrapeRequest_profile
        from .scrape_request_proxy import ScrapeRequest_proxy
        from .scrape_request_routing_mode import ScrapeRequest_routing_mode
        from .scrape_request_screenshot_selector import ScrapeRequest_screenshot_selector
        from .scrape_request_session import ScrapeRequest_session
        from .scrape_request_timeout_ms import ScrapeRequest_timeout_ms
        from .scrape_request_url import ScrapeRequest_url
        from .scrape_request_urls import ScrapeRequest_urls

        from .scrape_request_batch_identity_mode import ScrapeRequest_batch_identity_mode
        from .scrape_request_behavior_actions import ScrapeRequest_behavior_actions
        from .scrape_request_engine import ScrapeRequest_engine
        from .scrape_request_format import ScrapeRequest_format
        from .scrape_request_identity import ScrapeRequest_identity
        from .scrape_request_identity_country import ScrapeRequest_identity_country
        from .scrape_request_language import ScrapeRequest_language
        from .scrape_request_profile import ScrapeRequest_profile
        from .scrape_request_proxy import ScrapeRequest_proxy
        from .scrape_request_routing_mode import ScrapeRequest_routing_mode
        from .scrape_request_screenshot_selector import ScrapeRequest_screenshot_selector
        from .scrape_request_session import ScrapeRequest_session
        from .scrape_request_timeout_ms import ScrapeRequest_timeout_ms
        from .scrape_request_url import ScrapeRequest_url
        from .scrape_request_urls import ScrapeRequest_urls

        fields: dict[str, Callable[[Any], None]] = {
            "batch_identity_mode": lambda n : setattr(self, 'batch_identity_mode', n.get_enum_value(ScrapeRequest_batch_identity_mode)),
            "behavior_actions": lambda n : setattr(self, 'behavior_actions', n.get_object_value(ScrapeRequest_behavior_actions)),
            "chunk_tokens": lambda n : setattr(self, 'chunk_tokens', n.get_int_value()),
            "engine": lambda n : setattr(self, 'engine', n.get_enum_value(ScrapeRequest_engine)),
            "format": lambda n : setattr(self, 'format', n.get_enum_value(ScrapeRequest_format)),
            "full_page": lambda n : setattr(self, 'full_page', n.get_bool_value()),
            "identity": lambda n : setattr(self, 'identity', n.get_object_value(ScrapeRequest_identity)),
            "identity_country": lambda n : setattr(self, 'identity_country', n.get_object_value(ScrapeRequest_identity_country)),
            "include_citations": lambda n : setattr(self, 'include_citations', n.get_bool_value()),
            "language": lambda n : setattr(self, 'language', n.get_object_value(ScrapeRequest_language)),
            "profile": lambda n : setattr(self, 'profile', n.get_object_value(ScrapeRequest_profile)),
            "proxy": lambda n : setattr(self, 'proxy', n.get_object_value(ScrapeRequest_proxy)),
            "routing_mode": lambda n : setattr(self, 'routing_mode', n.get_enum_value(ScrapeRequest_routing_mode)),
            "screenshot": lambda n : setattr(self, 'screenshot', n.get_bool_value()),
            "screenshot_selector": lambda n : setattr(self, 'screenshot_selector', n.get_object_value(ScrapeRequest_screenshot_selector)),
            "session": lambda n : setattr(self, 'session', n.get_object_value(ScrapeRequest_session)),
            "stream": lambda n : setattr(self, 'stream', n.get_bool_value()),
            "timeout_ms": lambda n : setattr(self, 'timeout_ms', n.get_object_value(ScrapeRequest_timeout_ms)),
            "url": lambda n : setattr(self, 'url', n.get_object_value(ScrapeRequest_url)),
            "urls": lambda n : setattr(self, 'urls', n.get_object_value(ScrapeRequest_urls)),
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
        writer.write_enum_value("batch_identity_mode", self.batch_identity_mode)
        writer.write_object_value("behavior_actions", self.behavior_actions)
        writer.write_int_value("chunk_tokens", self.chunk_tokens)
        writer.write_enum_value("engine", self.engine)
        writer.write_enum_value("format", self.format)
        writer.write_bool_value("full_page", self.full_page)
        writer.write_object_value("identity", self.identity)
        writer.write_object_value("identity_country", self.identity_country)
        writer.write_bool_value("include_citations", self.include_citations)
        writer.write_object_value("language", self.language)
        writer.write_object_value("profile", self.profile)
        writer.write_object_value("proxy", self.proxy)
        writer.write_enum_value("routing_mode", self.routing_mode)
        writer.write_bool_value("screenshot", self.screenshot)
        writer.write_object_value("screenshot_selector", self.screenshot_selector)
        writer.write_object_value("session", self.session)
        writer.write_bool_value("stream", self.stream)
        writer.write_object_value("timeout_ms", self.timeout_ms)
        writer.write_object_value("url", self.url)
        writer.write_object_value("urls", self.urls)
        writer.write_additional_data_value(self.additional_data)
    

