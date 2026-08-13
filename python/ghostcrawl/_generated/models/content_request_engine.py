from enum import Enum

class ContentRequest_engine(str, Enum):
    Auto = "auto",
    Chrome = "chrome",
    Firefox = "firefox",
    Webkit = "webkit",

