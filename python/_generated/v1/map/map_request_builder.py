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
    from ...models.map_body import MapBody
    from ...models.map_response import MapResponse
    from ...models.problem_details import ProblemDetails

class MapRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/map
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new MapRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/map", path_parameters)
    
    async def post(self,body: MapBody, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[MapResponse]:
        """
        sitemap URL discovery. 1. The seed URL is validated against private/loopback/metadata targets. 2. The request is quota-checked. 3. URLs are discovered from the site's sitemaps. 4. Results are filtered to the same registrable domain by default. 5. An optional case-insensitive substring filter is applied to URLs. 6. Results are capped at 10000 regardless of the requested limit.
        param body: Firecrawl-compatible /v1/map request body. naming convention warnings for intentional camelCase).
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[MapResponse]
        """
        if body is None:
            raise TypeError("body cannot be null.")
        request_info = self.to_post_request_information(
            body, request_configuration
        )
        from ...models.problem_details import ProblemDetails

        error_mapping: dict[str, type[ParsableFactory]] = {
            "422": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from ...models.map_response import MapResponse

        return await self.request_adapter.send_async(request_info, MapResponse, error_mapping)
    
    def to_post_request_information(self,body: MapBody, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        sitemap URL discovery. 1. The seed URL is validated against private/loopback/metadata targets. 2. The request is quota-checked. 3. URLs are discovered from the site's sitemaps. 4. Results are filtered to the same registrable domain by default. 5. An optional case-insensitive substring filter is applied to URLs. 6. Results are capped at 10000 regardless of the requested limit.
        param body: Firecrawl-compatible /v1/map request body. naming convention warnings for intentional camelCase).
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
    
    def with_url(self,raw_url: str) -> MapRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: MapRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return MapRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class MapRequestBuilderPostRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

