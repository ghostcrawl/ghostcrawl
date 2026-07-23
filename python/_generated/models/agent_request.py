from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .agent_request_mode import AgentRequest_mode
    from .agent_request_task import AgentRequest_task
    from .proxy_config import ProxyConfig

@dataclass
class AgentRequest(Parsable):
    from .agent_request_mode import AgentRequest_mode

    # The mode property
    mode: Optional[AgentRequest_mode] = AgentRequest_mode("sync")
    # The api_key property
    api_key: Optional[str] = None
    # The callback_url property
    callback_url: Optional[str] = None
    # Optional stable profile identifier. When supplied on a successful sync `/v1/agent` call, the executed step trace is recorded into the in-process action cache (keyed by `(profile_id, task)`) and can be replayed via `POST /v1/agent/action-cache/replay`. Response payload includes `action_cache_recorded: true|false` so callers can confirm cache durability.
    profile_id: Optional[str] = None
    # The proxy property
    proxy: Optional[ProxyConfig] = None
    # Agent task payload; URL fields are policy-validated when present.
    task: Optional[AgentRequest_task] = None
    # The tenant_id property
    tenant_id: Optional[str] = None
    # The workspace_id property
    workspace_id: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> AgentRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: AgentRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return AgentRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .agent_request_mode import AgentRequest_mode
        from .agent_request_task import AgentRequest_task
        from .proxy_config import ProxyConfig

        from .agent_request_mode import AgentRequest_mode
        from .agent_request_task import AgentRequest_task
        from .proxy_config import ProxyConfig

        fields: dict[str, Callable[[Any], None]] = {
            "api_key": lambda n : setattr(self, 'api_key', n.get_str_value()),
            "callback_url": lambda n : setattr(self, 'callback_url', n.get_str_value()),
            "mode": lambda n : setattr(self, 'mode', n.get_enum_value(AgentRequest_mode)),
            "profile_id": lambda n : setattr(self, 'profile_id', n.get_str_value()),
            "proxy": lambda n : setattr(self, 'proxy', n.get_object_value(ProxyConfig)),
            "task": lambda n : setattr(self, 'task', n.get_object_value(AgentRequest_task)),
            "tenant_id": lambda n : setattr(self, 'tenant_id', n.get_str_value()),
            "workspace_id": lambda n : setattr(self, 'workspace_id', n.get_str_value()),
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
        writer.write_str_value("callback_url", self.callback_url)
        writer.write_enum_value("mode", self.mode)
        writer.write_str_value("profile_id", self.profile_id)
        writer.write_object_value("proxy", self.proxy)
        writer.write_object_value("task", self.task)
        writer.write_str_value("tenant_id", self.tenant_id)
        writer.write_str_value("workspace_id", self.workspace_id)
    

