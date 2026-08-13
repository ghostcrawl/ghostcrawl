from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .start.start_request_builder import StartRequestBuilder
    from .stop.stop_request_builder import StopRequestBuilder

class RecordingRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/sessions/{profile_-id}/recording
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new RecordingRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/sessions/{profile_%2Did}/recording", path_parameters)
    
    @property
    def start(self) -> StartRequestBuilder:
        """
        The start property
        """
        from .start.start_request_builder import StartRequestBuilder

        return StartRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def stop(self) -> StopRequestBuilder:
        """
        The stop property
        """
        from .stop.stop_request_builder import StopRequestBuilder

        return StopRequestBuilder(self.request_adapter, self.path_parameters)
    

