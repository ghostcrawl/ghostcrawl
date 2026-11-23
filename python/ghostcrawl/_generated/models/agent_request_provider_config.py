from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class AgentRequest_provider_config(Parsable):
    """
    Bring-your-own LLM connection settings for this request. Tenant and workspace are derived from your authenticated credentials and cannot be overridden here.
    """
    # Your model-provider API key for this request.
    api_key: Optional[str] = None
    # OpenAI-compatible chat completions base URL.
    base_url: Optional[str] = None
    # Model identifier used for the reasoning step.
    model: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> AgentRequest_provider_config:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: AgentRequest_provider_config
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return AgentRequest_provider_config()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "api_key": lambda n : setattr(self, 'api_key', n.get_str_value()),
            "base_url": lambda n : setattr(self, 'base_url', n.get_str_value()),
            "model": lambda n : setattr(self, 'model', n.get_str_value()),
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
        writer.write_str_value("api_key", self.api_key)
        writer.write_str_value("base_url", self.base_url)
        writer.write_str_value("model", self.model)
    

