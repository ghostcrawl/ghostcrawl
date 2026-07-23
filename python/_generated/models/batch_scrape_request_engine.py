from enum import Enum

class BatchScrapeRequest_engine(str, Enum):
    Auto = "auto",
    Chrome = "chrome",
    Firefox = "firefox",
    Webkit = "webkit",

