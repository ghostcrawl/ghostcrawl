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
    from ....models.problem_details import ProblemDetails
    from .cancel.cancel_request_builder import CancelRequestBuilder
    from .resume.resume_request_builder import ResumeRequestBuilder

class WithRun_ItemRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/crawl-runs/{run_id}
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new WithRun_ItemRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/crawl-runs/{run_id}{?timeout_s*,wait*}", path_parameters)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[WithRun_ItemRequestBuilderGetQueryParameters]] = None) -> Optional[bytes]:
        """
        status, plus OPT-IN long-poll. Default (``wait`` absent/false): instant status snapshot, behavior unchanged. ``?wait=true&timeout_s=N``: BLOCKS event-driven (same cross-worker `` signal as start-and-wait) until the run reaches a terminal state (completed|cancelled|failed|failed_resumable) or ``timeout_s`` elapses, THEN returns the run record (results included when completed). A timeout returns the CURRENT non-terminal run as HTTP 200, a long-poll, NOT an error. ``timeout_s`` defaults to 300 and is capped at a server-configured maximum (default 600).
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: bytes
        """
        request_info = self.to_get_request_information(
            request_configuration
        )
        from ....models.problem_details import ProblemDetails

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
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[WithRun_ItemRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        status, plus OPT-IN long-poll. Default (``wait`` absent/false): instant status snapshot, behavior unchanged. ``?wait=true&timeout_s=N``: BLOCKS event-driven (same cross-worker `` signal as start-and-wait) until the run reaches a terminal state (completed|cancelled|failed|failed_resumable) or ``timeout_s`` elapses, THEN returns the run record (results included when completed). A timeout returns the CURRENT non-terminal run as HTTP 200, a long-poll, NOT an error. ``timeout_s`` defaults to 300 and is capped at a server-configured maximum (default 600).
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> WithRun_ItemRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: WithRun_ItemRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return WithRun_ItemRequestBuilder(self.request_adapter, raw_url)
    
    @property
    def cancel(self) -> CancelRequestBuilder:
        """
        The cancel property
        """
        from .cancel.cancel_request_builder import CancelRequestBuilder

        return CancelRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def resume(self) -> ResumeRequestBuilder:
        """
        The resume property
        """
        from .resume.resume_request_builder import ResumeRequestBuilder

        return ResumeRequestBuilder(self.request_adapter, self.path_parameters)
    
    @dataclass
    class WithRun_ItemRequestBuilderGetQueryParameters():
        """
        status, plus OPT-IN long-poll. Default (``wait`` absent/false): instant status snapshot, behavior unchanged. ``?wait=true&timeout_s=N``: BLOCKS event-driven (same cross-worker `` signal as start-and-wait) until the run reaches a terminal state (completed|cancelled|failed|failed_resumable) or ``timeout_s`` elapses, THEN returns the run record (results included when completed). A timeout returns the CURRENT non-terminal run as HTTP 200, a long-poll, NOT an error. ``timeout_s`` defaults to 300 and is capped at a server-configured maximum (default 600).
        """
        timeout_s: Optional[int] = None

        wait: Optional[bool] = None

    
    @dataclass
    class WithRun_ItemRequestBuilderGetRequestConfiguration(RequestConfiguration[WithRun_ItemRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

