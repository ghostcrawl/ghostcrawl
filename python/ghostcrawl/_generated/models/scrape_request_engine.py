from enum import Enum

class ScrapeRequest_engine(str, Enum):
    Auto = "auto",
    Chrome = "chrome",
    Firefox = "firefox",
    Webkit = "webkit",

