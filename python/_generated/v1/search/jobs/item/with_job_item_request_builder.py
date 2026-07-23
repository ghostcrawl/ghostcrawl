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
    from .....models.problem_details import ProblemDetails

class WithJob_ItemRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/search/jobs/{job_id}
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new WithJob_ItemRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/search/jobs/{job_id}", path_parameters)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[bytes]:
        """
        200 + SearchResult when done (real result items = GREEN); 202 {status:"running"} while the extended rotation is still going (carrying ``deadline``/``poll_max_seconds`` so the client loop is bounded); 200 {status:"open", items:[]} on honest exhaustion (challenged/0-result, never a faked GREEN); 200 {status:"temporarily_unavailable"} when the deadline passes with the record still ``running`` (lost worker, retryable terminal); 404 if unknown/expired/foreign. Ownership-scoped: a job created by another tenant reads as 404. BOUNDED-TERMINAL CONTRACT (no infinite poll): every poll resolves to a terminal within the stamped deadline REGARDLESS of worker health. A 404 is TERMINAL, the job expired or is unknown; the query may be retried at a HUMAN pace after Retry-After, but a 404 must NEVER be auto-interpreted as "resubmit the same query in a tight loop" (that is the one behavior that turns a recoverable miss into an infinite loop). See the SDK/MCP wrapper.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: bytes
        """
        request_info = self.to_get_request_information(
            request_configuration
        )
        from .....models.problem_details import ProblemDetails

        error_mapping: dict[str, type[ParsableFactory]] = {
            "422": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        return await self.request_adapter.send_primitive_async(request_info, "bytes", error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        200 + SearchResult when done (real result items = GREEN); 202 {status:"running"} while the extended rotation is still going (carrying ``deadline``/``poll_max_seconds`` so the client loop is bounded); 200 {status:"open", items:[]} on honest exhaustion (challenged/0-result, never a faked GREEN); 200 {status:"temporarily_unavailable"} when the deadline passes with the record still ``running`` (lost worker, retryable terminal); 404 if unknown/expired/foreign. Ownership-scoped: a job created by another tenant reads as 404. BOUNDED-TERMINAL CONTRACT (no infinite poll): every poll resolves to a terminal within the stamped deadline REGARDLESS of worker health. A 404 is TERMINAL, the job expired or is unknown; the query may be retried at a HUMAN pace after Retry-After, but a 404 must NEVER be auto-interpreted as "resubmit the same query in a tight loop" (that is the one behavior that turns a recoverable miss into an infinite loop). See the SDK/MCP wrapper.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> WithJob_ItemRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: WithJob_ItemRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return WithJob_ItemRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class WithJob_ItemRequestBuilderGetRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

