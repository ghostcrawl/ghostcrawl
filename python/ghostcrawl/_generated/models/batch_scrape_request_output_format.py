from enum import Enum

class BatchScrapeRequest_output_format(str, Enum):
    Html = "html",
    Markdown = "markdown",
    Both = "both",

