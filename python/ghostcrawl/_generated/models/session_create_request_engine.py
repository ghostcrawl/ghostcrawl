from enum import Enum

class SessionCreateRequest_engine(str, Enum):
    Chrome = "chrome",
    Firefox = "firefox",
    Webkit = "webkit",
    Auto = "auto",

