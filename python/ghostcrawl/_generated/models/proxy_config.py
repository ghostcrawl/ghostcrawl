from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class ProxyConfig(Parsable):
    # The bypass property
    bypass: Optional[str] = None
    # The password property
    password: Optional[str] = None
    # Proxy URL with scheme and host:port.
    server: Optional[str] = None
    # The username property
    username: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ProxyConfig:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ProxyConfig
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ProxyConfig()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "bypass": lambda n : setattr(self, 'bypass', n.get_str_value()),
            "password": lambda n : setattr(self, 'password', n.get_str_value()),
            "server": lambda n : setattr(self, 'server', n.get_str_value()),
            "username": lambda n : setattr(self, 'username', n.get_str_value()),
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
        writer.write_str_value("bypass", self.bypass)
        writer.write_str_value("password", self.password)
        writer.write_str_value("server", self.server)
        writer.write_str_value("username", self.username)
    

