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
    from .detach.detach_request_builder import DetachRequestBuilder
    from .item.with_id_or_name_item_request_builder import WithId_or_nameItemRequestBuilder
    from .storage_states_post_request_body import StorageStatesPostRequestBody

class StorageStatesRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/storage-states
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new StorageStatesRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/storage-states{?cursor*,limit*}", path_parameters)
    
    def by_id_or_name(self,id_or_name: str) -> WithId_or_nameItemRequestBuilder:
        """
        Gets an item from the ghostcrawl.v1.storageStates.item collection
        param id_or_name: Unique identifier of the item
        Returns: WithId_or_nameItemRequestBuilder
        """
        if id_or_name is None:
            raise TypeError("id_or_name cannot be null.")
        from .item.with_id_or_name_item_request_builder import WithId_or_nameItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["id_or_name"] = id_or_name
        return WithId_or_nameItemRequestBuilder(self.request_adapter, url_tpl_params)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[StorageStatesRequestBuilderGetQueryParameters]] = None) -> Optional[bytes]:
        """
        owner-scoped cursor pagination.
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
    
    async def post(self,body: StorageStatesPostRequestBody, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[bytes]:
        """
        snapshot browser storage state from a live session. Captures the current cookies, localStorage, and session storage from the named active profile and saves it encrypted under the given name. Returns storage state metadata on success (credentials are never returned). Storage blobs over 5 MB return storage_state_too_large (400).
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
            "422": ProblemDetails,
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        return await self.request_adapter.send_primitive_async(request_info, "bytes", error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[StorageStatesRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        owner-scoped cursor pagination.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def to_post_request_information(self,body: StorageStatesPostRequestBody, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        snapshot browser storage state from a live session. Captures the current cookies, localStorage, and session storage from the named active profile and saves it encrypted under the given name. Returns storage state metadata on success (credentials are never returned). Storage blobs over 5 MB return storage_state_too_large (400).
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
    
    def with_url(self,raw_url: str) -> StorageStatesRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: StorageStatesRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return StorageStatesRequestBuilder(self.request_adapter, raw_url)
    
    @property
    def detach(self) -> DetachRequestBuilder:
        """
        The detach property
        """
        from .detach.detach_request_builder import DetachRequestBuilder

        return DetachRequestBuilder(self.request_adapter, self.path_parameters)
    
    @dataclass
    class StorageStatesRequestBuilderGetQueryParameters():
        """
        owner-scoped cursor pagination.
        """
        cursor: Optional[str] = None

        limit: Optional[int] = None

    
    @dataclass
    class StorageStatesRequestBuilderGetRequestConfiguration(RequestConfiguration[StorageStatesRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    
    @dataclass
    class StorageStatesRequestBuilderPostRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

