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
    from ...models.webhook_create_request import WebhookCreateRequest
    from ...models.webhook_create_response import WebhookCreateResponse
    from ...models.webhook_list_response import WebhookListResponse
    from .item.with_webhook_item_request_builder import WithWebhook_ItemRequestBuilder

class WebhooksRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/webhooks
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new WebhooksRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/webhooks{?created_at_from*,created_at_to*,cursor*,limit*,tags*}", path_parameters)
    
    def by_webhook_id(self,webhook_id: str) -> WithWebhook_ItemRequestBuilder:
        """
        Gets an item from the ghostcrawl.v1.webhooks.item collection
        param webhook_id: Unique identifier of the item
        Returns: WithWebhook_ItemRequestBuilder
        """
        if webhook_id is None:
            raise TypeError("webhook_id cannot be null.")
        from .item.with_webhook_item_request_builder import WithWebhook_ItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["webhook_id"] = webhook_id
        return WithWebhook_ItemRequestBuilder(self.request_adapter, url_tpl_params)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[WebhooksRequestBuilderGetQueryParameters]] = None) -> Optional[WebhookListResponse]:
        """
        cursor pagination. without it → 403.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[WebhookListResponse]
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
        from ...models.webhook_list_response import WebhookListResponse

        return await self.request_adapter.send_async(request_info, WebhookListResponse, error_mapping)
    
    async def post(self,body: WebhookCreateRequest, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[WebhookCreateResponse]:
        """
        Create a new webhook subscription. Returns the webhook plus the plaintext signing secret once. Store the secret immediately, it cannot be recovered; only rotation via /rotate-secret provides a new one.
        param body: Request body for POST /v1/webhooks.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[WebhookCreateResponse]
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
        from ...models.webhook_create_response import WebhookCreateResponse

        return await self.request_adapter.send_async(request_info, WebhookCreateResponse, error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[WebhooksRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        cursor pagination. without it → 403.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def to_post_request_information(self,body: WebhookCreateRequest, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        Create a new webhook subscription. Returns the webhook plus the plaintext signing secret once. Store the secret immediately, it cannot be recovered; only rotation via /rotate-secret provides a new one.
        param body: Request body for POST /v1/webhooks.
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
    
    def with_url(self,raw_url: str) -> WebhooksRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: WebhooksRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return WebhooksRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class WebhooksRequestBuilderGetQueryParameters():
        """
        cursor pagination. without it → 403.
        """
        created_at_from: Optional[str] = None

        created_at_to: Optional[str] = None

        cursor: Optional[str] = None

        limit: Optional[int] = None

        tags: Optional[str] = None

    
    @dataclass
    class WebhooksRequestBuilderGetRequestConfiguration(RequestConfiguration[WebhooksRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    
    @dataclass
    class WebhooksRequestBuilderPostRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

