from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .cookies_delete_body_domain import CookiesDeleteBody_domain
    from .cookies_delete_body_name import CookiesDeleteBody_name
    from .cookies_delete_body_path import CookiesDeleteBody_path

@dataclass
class CookiesDeleteBody(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The domain property
    domain: Optional[CookiesDeleteBody_domain] = None
    # The name property
    name: Optional[CookiesDeleteBody_name] = None
    # The path property
    path: Optional[CookiesDeleteBody_path] = None
    # The profile_id property
    profile_id: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> CookiesDeleteBody:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: CookiesDeleteBody
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return CookiesDeleteBody()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .cookies_delete_body_domain import CookiesDeleteBody_domain
        from .cookies_delete_body_name import CookiesDeleteBody_name
        from .cookies_delete_body_path import CookiesDeleteBody_path

        from .cookies_delete_body_domain import CookiesDeleteBody_domain
        from .cookies_delete_body_name import CookiesDeleteBody_name
        from .cookies_delete_body_path import CookiesDeleteBody_path

        fields: dict[str, Callable[[Any], None]] = {
            "domain": lambda n : setattr(self, 'domain', n.get_object_value(CookiesDeleteBody_domain)),
            "name": lambda n : setattr(self, 'name', n.get_object_value(CookiesDeleteBody_name)),
            "path": lambda n : setattr(self, 'path', n.get_object_value(CookiesDeleteBody_path)),
            "profile_id": lambda n : setattr(self, 'profile_id', n.get_str_value()),
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
        writer.write_object_value("name", self.name)
        writer.write_object_value("path", self.path)
        writer.write_str_value("profile_id", self.profile_id)
        writer.write_additional_data_value(self.additional_data)
    

