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
    from .extend.extend_request_builder import ExtendRequestBuilder
    from .pin.pin_request_builder import PinRequestBuilder
    from .recording.recording_request_builder import RecordingRequestBuilder
    from .release.release_request_builder import ReleaseRequestBuilder
    from .takeover.takeover_request_builder import TakeoverRequestBuilder
    from .takeover_release.takeover_release_request_builder import Takeover_releaseRequestBuilder
    from .takeover_token.takeover_token_request_builder import Takeover_tokenRequestBuilder
    from .terminate.terminate_request_builder import TerminateRequestBuilder

class Profile_ItemRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/sessions/{profile_-id}
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new Profile_ItemRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/sessions/{profile_%2Did}", path_parameters)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[bytes]:
        """
        return the session lease record (org-owned) or 404. Reads; a missing lease OR a cross-org lease → 404). tenant_id is not echoed.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: bytes
        """
        request_info = self.to_get_request_information(
            request_configuration
        )
        from ....models.problem_details import ProblemDetails

        error_mapping: dict[str, type[ParsableFactory]] = {
            "422": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        return await self.request_adapter.send_primitive_async(request_info, "bytes", error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        return the session lease record (org-owned) or 404. Reads; a missing lease OR a cross-org lease → 404). tenant_id is not echoed.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> Profile_ItemRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: Profile_ItemRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return Profile_ItemRequestBuilder(self.request_adapter, raw_url)
    
    @property
    def extend(self) -> ExtendRequestBuilder:
        """
        The extend property
        """
        from .extend.extend_request_builder import ExtendRequestBuilder

        return ExtendRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def pin(self) -> PinRequestBuilder:
        """
        The pin property
        """
        from .pin.pin_request_builder import PinRequestBuilder

        return PinRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def recording(self) -> RecordingRequestBuilder:
        """
        The recording property
        """
        from .recording.recording_request_builder import RecordingRequestBuilder

        return RecordingRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def release(self) -> ReleaseRequestBuilder:
        """
        The release property
        """
        from .release.release_request_builder import ReleaseRequestBuilder

        return ReleaseRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def takeover(self) -> TakeoverRequestBuilder:
        """
        The takeover property
        """
        from .takeover.takeover_request_builder import TakeoverRequestBuilder

        return TakeoverRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def takeover_release(self) -> Takeover_releaseRequestBuilder:
        """
        The takeover_release property
        """
        from .takeover_release.takeover_release_request_builder import Takeover_releaseRequestBuilder

        return Takeover_releaseRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def takeover_token(self) -> Takeover_tokenRequestBuilder:
        """
        The takeover_token property
        """
        from .takeover_token.takeover_token_request_builder import Takeover_tokenRequestBuilder

        return Takeover_tokenRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def terminate(self) -> TerminateRequestBuilder:
        """
        The terminate property
        """
        from .terminate.terminate_request_builder import TerminateRequestBuilder

        return TerminateRequestBuilder(self.request_adapter, self.path_parameters)
    
    @dataclass
    class Profile_ItemRequestBuilderGetRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

