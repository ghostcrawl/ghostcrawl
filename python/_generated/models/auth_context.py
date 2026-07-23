from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union
from uuid import UUID

@dataclass
class AuthContext(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The comp property
    comp: Optional[bool] = False
    # The tier property
    tier: Optional[str] = "free"
    # The is_admin property
    is_admin: Optional[bool] = None
    # The key_env property
    key_env: Optional[str] = None
    # The team_id property
    team_id: Optional[UUID] = None
    # The user_id property
    user_id: Optional[str] = None
    # The workspace_id property
    workspace_id: Optional[UUID] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> AuthContext:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: AuthContext
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return AuthContext()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        fields: dict[str, Callable[[Any], None]] = {
            "comp": lambda n : setattr(self, 'comp', n.get_bool_value()),
            "is_admin": lambda n : setattr(self, 'is_admin', n.get_bool_value()),
            "key_env": lambda n : setattr(self, 'key_env', n.get_str_value()),
            "team_id": lambda n : setattr(self, 'team_id', n.get_uuid_value()),
            "tier": lambda n : setattr(self, 'tier', n.get_str_value()),
            "user_id": lambda n : setattr(self, 'user_id', n.get_str_value()),
            "workspace_id": lambda n : setattr(self, 'workspace_id', n.get_uuid_value()),
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
        writer.write_bool_value("comp", self.comp)
        writer.write_bool_value("is_admin", self.is_admin)
        writer.write_str_value("key_env", self.key_env)
        writer.write_uuid_value("team_id", self.team_id)
        writer.write_str_value("tier", self.tier)
        writer.write_str_value("user_id", self.user_id)
        writer.write_uuid_value("workspace_id", self.workspace_id)
        writer.write_additional_data_value(self.additional_data)
    

