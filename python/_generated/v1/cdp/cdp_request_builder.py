from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .frame.frame_request_builder import FrameRequestBuilder
    from .url.url_request_builder import UrlRequestBuilder

class CdpRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/cdp
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new CdpRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/cdp", path_parameters)
    
    @property
    def frame(self) -> FrameRequestBuilder:
        """
        The frame property
        """
        from .frame.frame_request_builder import FrameRequestBuilder

        return FrameRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def url(self) -> UrlRequestBuilder:
        """
        The url property
        """
        from .url.url_request_builder import UrlRequestBuilder

        return UrlRequestBuilder(self.request_adapter, self.path_parameters)
    

