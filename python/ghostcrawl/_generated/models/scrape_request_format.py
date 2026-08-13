from enum import Enum

class ScrapeRequest_format(str, Enum):
    Html = "html",
    Markdown = "markdown",
    Pdf = "pdf",

