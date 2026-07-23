from enum import Enum

class PdfRequest_engine(str, Enum):
    Auto = "auto",
    Chrome = "chrome",
    Firefox = "firefox",
    Webkit = "webkit",

