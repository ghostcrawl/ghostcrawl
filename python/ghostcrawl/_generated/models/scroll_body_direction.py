from enum import Enum

class ScrollBody_direction(str, Enum):
    Up = "up",
    Down = "down",
    Top = "top",
    Bottom = "bottom",
    Into_view = "into_view",

