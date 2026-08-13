from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
from kiota_abstractions.default_query_parameters import QueryParameters
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.method import Method
from kiota_abstractions.request_adapter import RequestAdapter
from kiota_abstractions.request_information import RequestInformation
from kiota_abstractions.request_option import RequestOption
from kiota_abstractions.serialization import Parsable, ParsableFactory
from typing import Any, Optional, TYPE_CHECKING, Union
from warnings import warn

if TYPE_CHECKING:
    from ...models.problem_details import ProblemDetails
    from .crawl_runs_post_request_body import CrawlRunsPostRequestBody
    from .item.with_run_item_request_builder import WithRun_ItemRequestBuilder

class CrawlRunsRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/crawl-runs
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new CrawlRunsRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/crawl-runs{?created_at_from*,created_at_to*,cursor*,limit*,tags*}", path_parameters)
    
    def by_run_id(self,run_id: str) -> WithRun_ItemRequestBuilder:
        """
        Gets an item from the ghostcrawl.v1.crawlRuns.item collection
        param run_id: Unique identifier of the item
        Returns: WithRun_ItemRequestBuilder
        """
        if run_id is None:
            raise TypeError("run_id cannot be null.")
        from .item.with_run_item_request_builder import WithRun_ItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["run_id"] = run_id
        return WithRun_ItemRequestBuilder(self.request_adapter, url_tpl_params)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[CrawlRunsRequestBuilderGetQueryParameters]] = None) -> Optional[bytes]:
        """
        cursor pagination. {items, next_cursor, total_count}. change in; created_at_from > created_at_to → 400 (not 422). Error envelope for 403 unchanged (at error layer).
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: bytes
        """
        request_info = self.to_get_request_information(
            request_configuration
        )
        from ...models.problem_details import ProblemDetails

        error_mapping: dict[str, type[ParsableFactory]] = {
            "422": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        return await self.request_adapter.send_primitive_async(request_info, "bytes", error_mapping)
    
    async def post(self,body: CrawlRunsPostRequestBody, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[bytes]:
        """
        Start a crawl run
        param body: The request body
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: bytes
        """
        if body is None:
            raise TypeError("body cannot be null.")
        request_info = self.to_post_request_information(
            body, request_configuration
        )
        from ...models.problem_details import ProblemDetails

        error_mapping: dict[str, type[ParsableFactory]] = {
            "400": ProblemDetails,
            "401": ProblemDetails,
            "402": ProblemDetails,
            "404": ProblemDetails,
            "422": ProblemDetails,
            "429": ProblemDetails,
            "500": ProblemDetails,
            "503": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        return await self.request_adapter.send_primitive_async(request_info, "bytes", error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[CrawlRunsRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        cursor pagination. {items, next_cursor, total_count}. change in; created_at_from > created_at_to → 400 (not 422). Error envelope for 403 unchanged (at error layer).
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def to_post_request_information(self,body: CrawlRunsPostRequestBody, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        Start a crawl run
        param body: The request body
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        if body is None:
            raise TypeError("body cannot be null.")
        request_info = RequestInformation(Method.POST, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        request_info.set_content_from_parsable(self.request_adapter, "application/json", body)
        return request_info
    
    def with_url(self,raw_url: str) -> CrawlRunsRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: CrawlRunsRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return CrawlRunsRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class CrawlRunsRequestBuilderGetQueryParameters():
        """
        cursor pagination. {items, next_cursor, total_count}. change in; created_at_from > created_at_to → 400 (not 422). Error envelope for 403 unchanged (at error layer).
        """
        created_at_from: Optional[str] = None

        created_at_to: Optional[str] = None

        cursor: Optional[str] = None

        limit: Optional[int] = None

        tags: Optional[str] = None

    
    @dataclass
    class CrawlRunsRequestBuilderGetRequestConfiguration(RequestConfiguration[CrawlRunsRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    
    @dataclass
    class CrawlRunsRequestBuilderPostRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

