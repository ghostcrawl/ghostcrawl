from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .agent_request_task_steps import AgentRequest_task_steps

@dataclass
class AgentRequest_task(AdditionalDataHolder, Parsable):
    """
    Agent task payload; URL fields are policy-validated when present.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # The goal property
    goal: Optional[str] = None
    # The start_url property
    start_url: Optional[str] = None
    # Typed agent-step baseline contract (observe/act/extract).
    steps: Optional[list[AgentRequest_task_steps]] = None
    # The target_url property
    target_url: Optional[str] = None
    # The url property
    url: Optional[str] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> AgentRequest_task:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: AgentRequest_task
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return AgentRequest_task()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .agent_request_task_steps import AgentRequest_task_steps

        from .agent_request_task_steps import AgentRequest_task_steps

        fields: dict[str, Callable[[Any], None]] = {
            "goal": lambda n : setattr(self, 'goal', n.get_str_value()),
            "start_url": lambda n : setattr(self, 'start_url', n.get_str_value()),
            "steps": lambda n : setattr(self, 'steps', n.get_collection_of_object_values(AgentRequest_task_steps)),
            "target_url": lambda n : setattr(self, 'target_url', n.get_str_value()),
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
        writer.write_str_value("goal", self.goal)
        writer.write_str_value("start_url", self.start_url)
        writer.write_collection_of_object_values("steps", self.steps)
        writer.write_str_value("target_url", self.target_url)
        writer.write_str_value("url", self.url)
        writer.write_additional_data_value(self.additional_data)
    

