from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .screenshot_request_engine import ScreenshotRequest_engine
    from .screenshot_request_identity import ScreenshotRequest_identity
    from .screenshot_request_identity_country import ScreenshotRequest_identity_country
    from .screenshot_request_language import ScreenshotRequest_language
    from .screenshot_request_profile import ScreenshotRequest_profile
    from .screenshot_request_proxy import ScreenshotRequest_proxy
    from .screenshot_request_screenshot_selector import ScreenshotRequest_screenshot_selector

@dataclass
class ScreenshotRequest(AdditionalDataHolder, Parsable):
    """
    POST /v1/screenshot request body, capture a URL to a PNG screenshot.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    from .screenshot_request_engine import ScreenshotRequest_engine

    # Engine override (screenshot works on every engine).
    engine: Optional[ScreenshotRequest_engine] = ScreenshotRequest_engine("auto")
    # Capture the FULL document height instead of just the viewport.
    full_page: Optional[bool] = False
    # Re-use a persisted identity.
    identity: Optional[ScreenshotRequest_identity] = None
    # Two-letter country code to pin the exit country.
    identity_country: Optional[ScreenshotRequest_identity_country] = None
    # Browser language tag override (e.g. 'en-US').
    language: Optional[ScreenshotRequest_language] = None
    # Named persistent profile.
    profile: Optional[ScreenshotRequest_profile] = None
    # Override proxy URL for this request.
    proxy: Optional[ScreenshotRequest_proxy] = None
    # Clip to the first DOM element matching this CSS selector (element screenshot).
    screenshot_selector: Optional[ScreenshotRequest_screenshot_selector] = None
    # URL to capture.
    url: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ScreenshotRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ScreenshotRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ScreenshotRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .screenshot_request_engine import ScreenshotRequest_engine
        from .screenshot_request_identity import ScreenshotRequest_identity
        from .screenshot_request_identity_country import ScreenshotRequest_identity_country
        from .screenshot_request_language import ScreenshotRequest_language
        from .screenshot_request_profile import ScreenshotRequest_profile
        from .screenshot_request_proxy import ScreenshotRequest_proxy
        from .screenshot_request_screenshot_selector import ScreenshotRequest_screenshot_selector

        from .screenshot_request_engine import ScreenshotRequest_engine
        from .screenshot_request_identity import ScreenshotRequest_identity
        from .screenshot_request_identity_country import ScreenshotRequest_identity_country
        from .screenshot_request_language import ScreenshotRequest_language
        from .screenshot_request_profile import ScreenshotRequest_profile
        from .screenshot_request_proxy import ScreenshotRequest_proxy
        from .screenshot_request_screenshot_selector import ScreenshotRequest_screenshot_selector

        fields: dict[str, Callable[[Any], None]] = {
            "engine": lambda n : setattr(self, 'engine', n.get_enum_value(ScreenshotRequest_engine)),
            "full_page": lambda n : setattr(self, 'full_page', n.get_bool_value()),
            "identity": lambda n : setattr(self, 'identity', n.get_object_value(ScreenshotRequest_identity)),
            "identity_country": lambda n : setattr(self, 'identity_country', n.get_object_value(ScreenshotRequest_identity_country)),
            "language": lambda n : setattr(self, 'language', n.get_object_value(ScreenshotRequest_language)),
            "profile": lambda n : setattr(self, 'profile', n.get_object_value(ScreenshotRequest_profile)),
            "proxy": lambda n : setattr(self, 'proxy', n.get_object_value(ScreenshotRequest_proxy)),
            "screenshot_selector": lambda n : setattr(self, 'screenshot_selector', n.get_object_value(ScreenshotRequest_screenshot_selector)),
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
        writer.write_bool_value("full_page", self.full_page)
        writer.write_object_value("identity", self.identity)
        writer.write_object_value("identity_country", self.identity_country)
        writer.write_object_value("language", self.language)
        writer.write_object_value("profile", self.profile)
        writer.write_object_value("proxy", self.proxy)
        writer.write_object_value("screenshot_selector", self.screenshot_selector)
        writer.write_str_value("url", self.url)
        writer.write_additional_data_value(self.additional_data)
    

