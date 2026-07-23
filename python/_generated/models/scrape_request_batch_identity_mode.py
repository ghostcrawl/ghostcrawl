from enum import Enum

class ScrapeRequest_batch_identity_mode(str, Enum):
    Persist = "persist",
    Randomize = "randomize",

