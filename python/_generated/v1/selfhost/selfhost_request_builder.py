from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .byo.byo_request_builder import ByoRequestBuilder

class SelfhostRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/selfhost
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new SelfhostRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/selfhost", path_parameters)
    
    @property
    def byo(self) -> ByoRequestBuilder:
        """
        The byo property
        """
        from .byo.byo_request_builder import ByoRequestBuilder

        return ByoRequestBuilder(self.request_adapter, self.path_parameters)
    

