from enum import Enum

class AgentRequest_task_steps_type(str, Enum):
    Act = "act",
    Observe = "observe",
    Extract = "extract",

