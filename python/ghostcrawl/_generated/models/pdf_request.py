from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .pdf_request_engine import PdfRequest_engine
    from .pdf_request_identity import PdfRequest_identity
    from .pdf_request_identity_country import PdfRequest_identity_country
    from .pdf_request_language import PdfRequest_language
    from .pdf_request_profile import PdfRequest_profile
    from .pdf_request_proxy import PdfRequest_proxy

@dataclass
class PdfRequest(AdditionalDataHolder, Parsable):
    """
    POST /v1/pdf request body, render a URL to PDF. Renders the target URL to a PDF document. Supported on Chrome identities; requests that resolve to a Firefox or WebKit identity return 400 pdf_engine_unsupported. Security: - The URL is validated against private/loopback/metadata targets. - All traffic egresses through your configured proxy. - Subject to your daily request quota.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    from .pdf_request_engine import PdfRequest_engine

    # Engine override. PDF is chrome-only; 'firefox' or 'webkit' returns 400 pdf_engine_unsupported immediately (before dispatch).
    engine: Optional[PdfRequest_engine] = PdfRequest_engine("auto")
    # Re-use a persisted identity.
    identity: Optional[PdfRequest_identity] = None
    # Two-letter country code to pin the exit country.
    identity_country: Optional[PdfRequest_identity_country] = None
    # Browser language tag override (e.g. 'en-US').
    language: Optional[PdfRequest_language] = None
    # Named persistent profile.
    profile: Optional[PdfRequest_profile] = None
    # Override proxy URL for this request.
    proxy: Optional[PdfRequest_proxy] = None
    # URL to render as PDF.
    url: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> PdfRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: PdfRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return PdfRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .pdf_request_engine import PdfRequest_engine
        from .pdf_request_identity import PdfRequest_identity
        from .pdf_request_identity_country import PdfRequest_identity_country
        from .pdf_request_language import PdfRequest_language
        from .pdf_request_profile import PdfRequest_profile
        from .pdf_request_proxy import PdfRequest_proxy

        from .pdf_request_engine import PdfRequest_engine
        from .pdf_request_identity import PdfRequest_identity
        from .pdf_request_identity_country import PdfRequest_identity_country
        from .pdf_request_language import PdfRequest_language
        from .pdf_request_profile import PdfRequest_profile
        from .pdf_request_proxy import PdfRequest_proxy

        fields: dict[str, Callable[[Any], None]] = {
            "engine": lambda n : setattr(self, 'engine', n.get_enum_value(PdfRequest_engine)),
            "identity": lambda n : setattr(self, 'identity', n.get_object_value(PdfRequest_identity)),
            "identity_country": lambda n : setattr(self, 'identity_country', n.get_object_value(PdfRequest_identity_country)),
            "language": lambda n : setattr(self, 'language', n.get_object_value(PdfRequest_language)),
            "profile": lambda n : setattr(self, 'profile', n.get_object_value(PdfRequest_profile)),
            "proxy": lambda n : setattr(self, 'proxy', n.get_object_value(PdfRequest_proxy)),
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
        writer.write_object_value("identity", self.identity)
        writer.write_object_value("identity_country", self.identity_country)
        writer.write_object_value("language", self.language)
        writer.write_object_value("profile", self.profile)
        writer.write_object_value("proxy", self.proxy)
        writer.write_str_value("url", self.url)
        writer.write_additional_data_value(self.additional_data)
    

