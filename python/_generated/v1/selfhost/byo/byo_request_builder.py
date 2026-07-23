from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .behavior.behavior_request_builder import BehaviorRequestBuilder
    from .identity.identity_request_builder import IdentityRequestBuilder
    from .proxy.proxy_request_builder import ProxyRequestBuilder

class ByoRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/selfhost/byo
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new ByoRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/selfhost/byo", path_parameters)
    
    @property
    def behavior(self) -> BehaviorRequestBuilder:
        """
        The behavior property
        """
        from .behavior.behavior_request_builder import BehaviorRequestBuilder

        return BehaviorRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def identity(self) -> IdentityRequestBuilder:
        """
        The identity property
        """
        from .identity.identity_request_builder import IdentityRequestBuilder

        return IdentityRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def proxy(self) -> ProxyRequestBuilder:
        """
        The proxy property
        """
        from .proxy.proxy_request_builder import ProxyRequestBuilder

        return ProxyRequestBuilder(self.request_adapter, self.path_parameters)
    

