from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .item.with_job_item_request_builder import WithJob_ItemRequestBuilder

class JobsRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/search/jobs
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new JobsRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/search/jobs", path_parameters)
    
    def by_job_id(self,job_id: str) -> WithJob_ItemRequestBuilder:
        """
        Gets an item from the ghostcrawl.v1.search.jobs.item collection
        param job_id: Search job id from a 202 /v1/search handoff.
        Returns: WithJob_ItemRequestBuilder
        """
        if job_id is None:
            raise TypeError("job_id cannot be null.")
        from .item.with_job_item_request_builder import WithJob_ItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["job_id"] = job_id
        return WithJob_ItemRequestBuilder(self.request_adapter, url_tpl_params)
    

