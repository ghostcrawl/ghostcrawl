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
    from ...models.scrape_request import ScrapeRequest
    from ...models.scrape_result import ScrapeResult
    from .batch.batch_request_builder import BatchRequestBuilder

class ScrapeRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/scrape
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new ScrapeRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/scrape", path_parameters)
    
    async def post(self,body: ScrapeRequest, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[ScrapeResult]:
        """
        Bearer-gated scrape with identity field. Accepts: ``identity: "id_."`` Re-use a persisted identity (no quota charge). - ``identity_spec: {.}`` Inline identity creation (counts against quota). - neither Host-identity fallback; warns in response. - Both → 422 invalid_request. is unreachable from this route, profile.identity_id is always populated. stream=True branch returns text/event-stream with per-tenant cap.
        param body: POST /v1/scrape request body (-03 identity-aware shape).
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[ScrapeResult]
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
            "422": ProblemDetails,
            "429": ProblemDetails,
            "500": ProblemDetails,
            "503": ProblemDetails,
            "504": ProblemDetails,
            "XXX": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from ...models.scrape_result import ScrapeResult

        return await self.request_adapter.send_async(request_info, ScrapeResult, error_mapping)
    
    def to_post_request_information(self,body: ScrapeRequest, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        Bearer-gated scrape with identity field. Accepts: ``identity: "id_."`` Re-use a persisted identity (no quota charge). - ``identity_spec: {.}`` Inline identity creation (counts against quota). - neither Host-identity fallback; warns in response. - Both → 422 invalid_request. is unreachable from this route, profile.identity_id is always populated. stream=True branch returns text/event-stream with per-tenant cap.
        param body: POST /v1/scrape request body (-03 identity-aware shape).
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
    
    def with_url(self,raw_url: str) -> ScrapeRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: ScrapeRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return ScrapeRequestBuilder(self.request_adapter, raw_url)
    
    @property
    def batch(self) -> BatchRequestBuilder:
        """
        The batch property
        """
        from .batch.batch_request_builder import BatchRequestBuilder

        return BatchRequestBuilder(self.request_adapter, self.path_parameters)
    
    @dataclass
    class ScrapeRequestBuilderPostRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

