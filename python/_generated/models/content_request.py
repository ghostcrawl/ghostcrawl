from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .content_request_engine import ContentRequest_engine
    from .content_request_format import ContentRequest_format
    from .content_request_identity import ContentRequest_identity
    from .content_request_identity_country import ContentRequest_identity_country
    from .content_request_language import ContentRequest_language
    from .content_request_profile import ContentRequest_profile
    from .content_request_proxy import ContentRequest_proxy

@dataclass
class ContentRequest(AdditionalDataHolder, Parsable):
    """
    POST /v1/content request body, render a URL and return its content.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    from .content_request_engine import ContentRequest_engine

    # Engine override (content works on every engine).
    engine: Optional[ContentRequest_engine] = ContentRequest_engine("auto")
    from .content_request_format import ContentRequest_format

    # Content format: rendered post-JS 'html' (default) or 'markdown'.
    format: Optional[ContentRequest_format] = ContentRequest_format("html")
    # Re-use a persisted identity.
    identity: Optional[ContentRequest_identity] = None
    # Two-letter country code to pin the exit country.
    identity_country: Optional[ContentRequest_identity_country] = None
    # Browser language tag override (e.g. 'en-US').
    language: Optional[ContentRequest_language] = None
    # Named persistent profile.
    profile: Optional[ContentRequest_profile] = None
    # Override proxy URL for this request.
    proxy: Optional[ContentRequest_proxy] = None
    # URL to render and return content for.
    url: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ContentRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ContentRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ContentRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .content_request_engine import ContentRequest_engine
        from .content_request_format import ContentRequest_format
        from .content_request_identity import ContentRequest_identity
        from .content_request_identity_country import ContentRequest_identity_country
        from .content_request_language import ContentRequest_language
        from .content_request_profile import ContentRequest_profile
        from .content_request_proxy import ContentRequest_proxy

        from .content_request_engine import ContentRequest_engine
        from .content_request_format import ContentRequest_format
        from .content_request_identity import ContentRequest_identity
        from .content_request_identity_country import ContentRequest_identity_country
        from .content_request_language import ContentRequest_language
        from .content_request_profile import ContentRequest_profile
        from .content_request_proxy import ContentRequest_proxy

        fields: dict[str, Callable[[Any], None]] = {
            "engine": lambda n : setattr(self, 'engine', n.get_enum_value(ContentRequest_engine)),
            "format": lambda n : setattr(self, 'format', n.get_enum_value(ContentRequest_format)),
            "identity": lambda n : setattr(self, 'identity', n.get_object_value(ContentRequest_identity)),
            "identity_country": lambda n : setattr(self, 'identity_country', n.get_object_value(ContentRequest_identity_country)),
            "language": lambda n : setattr(self, 'language', n.get_object_value(ContentRequest_language)),
            "profile": lambda n : setattr(self, 'profile', n.get_object_value(ContentRequest_profile)),
            "proxy": lambda n : setattr(self, 'proxy', n.get_object_value(ContentRequest_proxy)),
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
        writer.write_enum_value("engine", self.engine)
        writer.write_enum_value("format", self.format)
        writer.write_object_value("identity", self.identity)
        writer.write_object_value("identity_country", self.identity_country)
        writer.write_object_value("language", self.language)
        writer.write_object_value("profile", self.profile)
        writer.write_object_value("proxy", self.proxy)
        writer.write_str_value("url", self.url)
        writer.write_additional_data_value(self.additional_data)
    

