from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

@dataclass
class UploadBody(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The content_base64 property
    content_base64: Optional[str] = None
    # The filename property
    filename: Optional[str] = None
    # The mime property
    mime: Optional[str] = None
    # The profile_id property
    profile_id: Optional[str] = None
    # The selector property
    selector: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> UploadBody:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: UploadBody
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return UploadBody()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "content_base64": lambda n : setattr(self, 'content_base64', n.get_str_value()),
            "filename": lambda n : setattr(self, 'filename', n.get_str_value()),
            "mime": lambda n : setattr(self, 'mime', n.get_str_value()),
            "profile_id": lambda n : setattr(self, 'profile_id', n.get_str_value()),
            "selector": lambda n : setattr(self, 'selector', n.get_str_value()),
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
        writer.write_str_value("content_base64", self.content_base64)
        writer.write_str_value("filename", self.filename)
        writer.write_str_value("mime", self.mime)
        writer.write_str_value("profile_id", self.profile_id)
        writer.write_str_value("selector", self.selector)
        writer.write_additional_data_value(self.additional_data)
    

