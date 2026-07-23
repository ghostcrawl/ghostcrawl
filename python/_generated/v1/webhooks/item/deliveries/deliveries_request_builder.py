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
    from .....models.webhook_delivery_list_response import WebhookDeliveryListResponse
    from .item.with_delivery_item_request_builder import WithDelivery_ItemRequestBuilder

class DeliveriesRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/webhooks/{webhook_id}/deliveries
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new DeliveriesRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/webhooks/{webhook_id}/deliveries{?created_at_from*,created_at_to*,cursor*,limit*,tags*}", path_parameters)
    
    def by_delivery_id(self,delivery_id: str) -> WithDelivery_ItemRequestBuilder:
        """
        Gets an item from the ghostcrawl.v1.webhooks.item.deliveries.item collection
        param delivery_id: Unique identifier of the item
        Returns: WithDelivery_ItemRequestBuilder
        """
        if delivery_id is None:
            raise TypeError("delivery_id cannot be null.")
        from .item.with_delivery_item_request_builder import WithDelivery_ItemRequestBuilder

        url_tpl_params = get_path_parameters(self.path_parameters)
        url_tpl_params["delivery_id"] = delivery_id
        return WithDelivery_ItemRequestBuilder(self.request_adapter, url_tpl_params)
    
    async def get(self,request_configuration: Optional[RequestConfiguration[DeliveriesRequestBuilderGetQueryParameters]] = None) -> Optional[WebhookDeliveryListResponse]:
        """
        GET /v1/webhooks/{webhook_id}/deliveries.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[WebhookDeliveryListResponse]
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
        from .....models.webhook_delivery_list_response import WebhookDeliveryListResponse

        return await self.request_adapter.send_async(request_info, WebhookDeliveryListResponse, error_mapping)
    
    def to_get_request_information(self,request_configuration: Optional[RequestConfiguration[DeliveriesRequestBuilderGetQueryParameters]] = None) -> RequestInformation:
        """
        GET /v1/webhooks/{webhook_id}/deliveries.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: RequestInformation
        """
        request_info = RequestInformation(Method.GET, self.url_template, self.path_parameters)
        request_info.configure(request_configuration)
        request_info.headers.try_add("Accept", "application/json")
        return request_info
    
    def with_url(self,raw_url: str) -> DeliveriesRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: DeliveriesRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return DeliveriesRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class DeliveriesRequestBuilderGetQueryParameters():
        """
        GET /v1/webhooks/{webhook_id}/deliveries.
        """
        created_at_from: Optional[str] = None

        created_at_to: Optional[str] = None

        cursor: Optional[str] = None

        limit: Optional[int] = None

        tags: Optional[str] = None

    
    @dataclass
    class DeliveriesRequestBuilderGetRequestConfiguration(RequestConfiguration[DeliveriesRequestBuilderGetQueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

