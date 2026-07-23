from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .extend.extend_request_builder import ExtendRequestBuilder
    from .pin.pin_request_builder import PinRequestBuilder
    from .recording.recording_request_builder import RecordingRequestBuilder
    from .release.release_request_builder import ReleaseRequestBuilder
    from .takeover.takeover_request_builder import TakeoverRequestBuilder
    from .takeover_release.takeover_release_request_builder import Takeover_releaseRequestBuilder
    from .takeover_token.takeover_token_request_builder import Takeover_tokenRequestBuilder

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
    

