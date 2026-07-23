from enum import Enum

class ScreenshotRequest_engine(str, Enum):
    Auto = "auto",
    Chrome = "chrome",
    Firefox = "firefox",
    Webkit = "webkit",

