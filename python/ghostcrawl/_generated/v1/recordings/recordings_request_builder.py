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
    from .item.recording_item_request_builder import Recording_ItemRequestBuilder

class RecordingsRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/recordings
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new RecordingsRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/recordings{?created_at_from*,created_at_to*,cursor*,limit*,tags*}", path_parameters)
    
    def by_recording_id(self,recording_id: str) -> Recording_ItemRequestBuilder:
        """
        Gets an item from the ghostcrawl.v1.recordings.item collection
        param recording_id: Unique identifier of the item
        Returns: Recording_ItemRequestBuilder
        """
        if recording_id is None:
            raise TypeError("recording_id cannot be null.")
        from .item.recording_item_request_builder import Recording_ItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["recording_%2Did"] = recording_id
        return Recording_ItemRequestBuilder(self.request_adapter, url_tpl_params)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[RecordingsRequestBuilderGetQueryParameters]] = None) -> Optional[bytes]:
        """
        cursor pagination. items[*] shape unchanged. created_at_from > created_at_to → 400 (not 422).
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
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[RecordingsRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        cursor pagination. items[*] shape unchanged. created_at_from > created_at_to → 400 (not 422).
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> RecordingsRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: RecordingsRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return RecordingsRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class RecordingsRequestBuilderGetQueryParameters():
        """
        cursor pagination. items[*] shape unchanged. created_at_from > created_at_to → 400 (not 422).
        """
        created_at_from: Optional[str] = None

        created_at_to: Optional[str] = None

        cursor: Optional[str] = None

        limit: Optional[int] = None

        tags: Optional[str] = None

    
    @dataclass
    class RecordingsRequestBuilderGetRequestConfiguration(RequestConfiguration[RecordingsRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

