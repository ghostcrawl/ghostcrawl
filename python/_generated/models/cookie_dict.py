from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .cookie_dict_domain import CookieDict_domain
    from .cookie_dict_expires import CookieDict_expires
    from .cookie_dict_http_only import CookieDict_httpOnly
    from .cookie_dict_path import CookieDict_path
    from .cookie_dict_same_site import CookieDict_sameSite
    from .cookie_dict_secure import CookieDict_secure
    from .cookie_dict_url import CookieDict_url

@dataclass
class CookieDict(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The domain property
    domain: Optional[CookieDict_domain] = None
    # The expires property
    expires: Optional[CookieDict_expires] = None
    # The httpOnly property
    http_only: Optional[CookieDict_httpOnly] = None
    # The name property
    name: Optional[str] = None
    # The path property
    path: Optional[CookieDict_path] = None
    # The sameSite property
    same_site: Optional[CookieDict_sameSite] = None
    # The secure property
    secure: Optional[CookieDict_secure] = None
    # The url property
    url: Optional[CookieDict_url] = None
    # The value property
    value: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> CookieDict:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: CookieDict
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return CookieDict()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .cookie_dict_domain import CookieDict_domain
        from .cookie_dict_expires import CookieDict_expires
        from .cookie_dict_http_only import CookieDict_httpOnly
        from .cookie_dict_path import CookieDict_path
        from .cookie_dict_same_site import CookieDict_sameSite
        from .cookie_dict_secure import CookieDict_secure
        from .cookie_dict_url import CookieDict_url

        from .cookie_dict_domain import CookieDict_domain
        from .cookie_dict_expires import CookieDict_expires
        from .cookie_dict_http_only import CookieDict_httpOnly
        from .cookie_dict_path import CookieDict_path
        from .cookie_dict_same_site import CookieDict_sameSite
        from .cookie_dict_secure import CookieDict_secure
        from .cookie_dict_url import CookieDict_url

        fields: dict[str, Callable[[Any], None]] = {
            "domain": lambda n : setattr(self, 'domain', n.get_object_value(CookieDict_domain)),
            "expires": lambda n : setattr(self, 'expires', n.get_object_value(CookieDict_expires)),
            "httpOnly": lambda n : setattr(self, 'http_only', n.get_object_value(CookieDict_httpOnly)),
            "name": lambda n : setattr(self, 'name', n.get_str_value()),
            "path": lambda n : setattr(self, 'path', n.get_object_value(CookieDict_path)),
            "sameSite": lambda n : setattr(self, 'same_site', n.get_object_value(CookieDict_sameSite)),
            "secure": lambda n : setattr(self, 'secure', n.get_object_value(CookieDict_secure)),
            "url": lambda n : setattr(self, 'url', n.get_object_value(CookieDict_url)),
            "value": lambda n : setattr(self, 'value', n.get_str_value()),
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
        writer.write_object_value("domain", self.domain)
        writer.write_object_value("expires", self.expires)
        writer.write_object_value("httpOnly", self.http_only)
        writer.write_str_value("name", self.name)
        writer.write_object_value("path", self.path)
        writer.write_object_value("sameSite", self.same_site)
        writer.write_object_value("secure", self.secure)
        writer.write_object_value("url", self.url)
        writer.write_str_value("value", self.value)
        writer.write_additional_data_value(self.additional_data)
    

