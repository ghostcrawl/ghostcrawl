from enum import Enum

class CdpInputRequest_step_type(str, Enum):
    Navigate = "navigate",
    Click = "click",
    Type = "type",

