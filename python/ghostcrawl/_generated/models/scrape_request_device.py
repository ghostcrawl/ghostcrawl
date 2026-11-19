from enum import Enum

class ScrapeRequest_device(str, Enum):
    Random = "random",
    Random_desktop = "random_desktop",
    Random_mobile = "random_mobile",
    Random_windows = "random_windows",
    Random_android = "random_android",
    Random_ios = "random_ios",

