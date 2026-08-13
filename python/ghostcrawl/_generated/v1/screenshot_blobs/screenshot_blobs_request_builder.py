from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .item.with_ref_item_request_builder import WithRefItemRequestBuilder

class ScreenshotBlobsRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/screenshot-blobs
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new ScreenshotBlobsRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/screenshot-blobs", path_parameters)
    
    def by_ref(self,ref: str) -> WithRefItemRequestBuilder:
        """
        Gets an item from the ghostcrawl.v1.screenshotBlobs.item collection
        param ref: Unique identifier of the item
        Returns: WithRefItemRequestBuilder
        """
        if ref is None:
            raise TypeError("ref cannot be null.")
        from .item.with_ref_item_request_builder import WithRefItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["ref"] = ref
        return WithRefItemRequestBuilder(self.request_adapter, url_tpl_params)
    

