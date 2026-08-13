from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .cookies.cookies_request_builder import CookiesRequestBuilder
    from .dom_snapshot.dom_snapshot_request_builder import Dom_snapshotRequestBuilder
    from .download.download_request_builder import DownloadRequestBuilder
    from .eval.eval_request_builder import EvalRequestBuilder
    from .har.har_request_builder import HarRequestBuilder
    from .scroll.scroll_request_builder import ScrollRequestBuilder
    from .upload.upload_request_builder import UploadRequestBuilder
    from .wait.wait_request_builder import WaitRequestBuilder

class PageRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/page
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new PageRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/page", path_parameters)
    
    @property
    def cookies(self) -> CookiesRequestBuilder:
        """
        The cookies property
        """
        from .cookies.cookies_request_builder import CookiesRequestBuilder

        return CookiesRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def dom_snapshot(self) -> Dom_snapshotRequestBuilder:
        """
        The dom_snapshot property
        """
        from .dom_snapshot.dom_snapshot_request_builder import Dom_snapshotRequestBuilder

        return Dom_snapshotRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def download(self) -> DownloadRequestBuilder:
        """
        The download property
        """
        from .download.download_request_builder import DownloadRequestBuilder

        return DownloadRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def eval(self) -> EvalRequestBuilder:
        """
        The eval property
        """
        from .eval.eval_request_builder import EvalRequestBuilder

        return EvalRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def har(self) -> HarRequestBuilder:
        """
        The har property
        """
        from .har.har_request_builder import HarRequestBuilder

        return HarRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def scroll(self) -> ScrollRequestBuilder:
        """
        The scroll property
        """
        from .scroll.scroll_request_builder import ScrollRequestBuilder

        return ScrollRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def upload(self) -> UploadRequestBuilder:
        """
        The upload property
        """
        from .upload.upload_request_builder import UploadRequestBuilder

        return UploadRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def wait(self) -> WaitRequestBuilder:
        """
        The wait property
        """
        from .wait.wait_request_builder import WaitRequestBuilder

        return WaitRequestBuilder(self.request_adapter, self.path_parameters)
    

