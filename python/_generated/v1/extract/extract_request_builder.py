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
    from ...models.extract_request import ExtractRequest
    from ...models.problem_details import ProblemDetails
    from .extract_post_response import ExtractPostResponse

class ExtractRequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1/extract
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new ExtractRequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1/extract", path_parameters)
    
    async def post(self,body: ExtractRequest, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> Optional[ExtractPostResponse]:
        """
        structured extraction (deterministic default) + bring-your-own-model extraction. Two modes (selected by model_provider): DETERMINISTIC (model_provider absent, default): 1. The schema is validated (input guard). 2. The URL is validated against private/loopback/metadata targets. 3. The page is fetched and rendered. 4. Structured data is extracted via CSS/regex/keyword rules. 5. The result is validated against the schema, 422 on mismatch (field path only). Returns {"url","data","token_estimate"}. BRING-YOUR-OWN-MODEL (model_provider present): 1. Target URLs are resolved (urls or [url]). 2. The schema is validated if present. 3. At least one of prompt or schema is required, 400 prompt_or_schema_required otherwise. 4. Model credentials are validated, 400 invalid_model_provider on error (the message never echoes the key). 5. Every target URL is validated before fetching, 400 ssrf_blocked. 6. Each URL is fetched and converted to clean Markdown. 7. Your connected model performs the extraction. 8. With a schema present, the result is validated, 422 on mismatch. Returns {"urls","data","token_estimate"}. Security: 401 without a valid Bearer token. - model_provider.api_key is request-scoped: never persisted, logged, or echoed. - Error responses never echo the schema body, fetched content, or credentials.
        param body: POST /v1/extract request body, schema-driven extraction (deterministic) + bring-your-own-model extraction. Two extraction modes: - Deterministic (default, model_provider absent): CSS/regex/keyword extraction. Requires 'schema'. Returns {"url","data","token_estimate"}. - Bring-your-own-model (model_provider present): GhostCrawl fetches and prepares clean Markdown; your connected model performs the semantic extraction (you are not billed for model inference here, only the request quota). Returns {"urls","data","token_estimate"}. Security notes: - The 'schema' field is validated before any fetch (fail-fast input guard). - URLs are validated against private, loopback, and metadata targets before any fetch. - Error responses never echo the schema body, fetched content, or model credentials. - model_provider.api_key is request-scoped only: never persisted, logged, or returned in any response body or error message.
        param request_configuration: Configuration for the request such as headers, query parameters, and middleware options.
        Returns: Optional[ExtractPostResponse]
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
        }
        if not self.request_adapter:
            raise Exception("Http core is null") 
        from .extract_post_response import ExtractPostResponse

        return await self.request_adapter.send_async(request_info, ExtractPostResponse, error_mapping)
    
    def to_post_request_information(self,body: ExtractRequest, request_configuration: Optional[RequestConfiguration[QueryParameters]] = None) -> RequestInformation:
        """
        structured extraction (deterministic default) + bring-your-own-model extraction. Two modes (selected by model_provider): DETERMINISTIC (model_provider absent, default): 1. The schema is validated (input guard). 2. The URL is validated against private/loopback/metadata targets. 3. The page is fetched and rendered. 4. Structured data is extracted via CSS/regex/keyword rules. 5. The result is validated against the schema, 422 on mismatch (field path only). Returns {"url","data","token_estimate"}. BRING-YOUR-OWN-MODEL (model_provider present): 1. Target URLs are resolved (urls or [url]). 2. The schema is validated if present. 3. At least one of prompt or schema is required, 400 prompt_or_schema_required otherwise. 4. Model credentials are validated, 400 invalid_model_provider on error (the message never echoes the key). 5. Every target URL is validated before fetching, 400 ssrf_blocked. 6. Each URL is fetched and converted to clean Markdown. 7. Your connected model performs the extraction. 8. With a schema present, the result is validated, 422 on mismatch. Returns {"urls","data","token_estimate"}. Security: 401 without a valid Bearer token. - model_provider.api_key is request-scoped: never persisted, logged, or echoed. - Error responses never echo the schema body, fetched content, or credentials.
        param body: POST /v1/extract request body, schema-driven extraction (deterministic) + bring-your-own-model extraction. Two extraction modes: - Deterministic (default, model_provider absent): CSS/regex/keyword extraction. Requires 'schema'. Returns {"url","data","token_estimate"}. - Bring-your-own-model (model_provider present): GhostCrawl fetches and prepares clean Markdown; your connected model performs the semantic extraction (you are not billed for model inference here, only the request quota). Returns {"urls","data","token_estimate"}. Security notes: - The 'schema' field is validated before any fetch (fail-fast input guard). - URLs are validated against private, loopback, and metadata targets before any fetch. - Error responses never echo the schema body, fetched content, or model credentials. - model_provider.api_key is request-scoped only: never persisted, logged, or returned in any response body or error message.
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
    
    def with_url(self,raw_url: str) -> ExtractRequestBuilder:
        """
        Returns a request builder with the provided arbitrary URL. Using this method means any other path or query parameters are ignored.
        param raw_url: The raw URL to use for the request builder.
        Returns: ExtractRequestBuilder
        """
        if raw_url is None:
            raise TypeError("raw_url cannot be null.")
        return ExtractRequestBuilder(self.request_adapter, raw_url)
    
    @dataclass
    class ExtractRequestBuilderPostRequestConfiguration(RequestConfiguration[QueryParameters]):
        """
        Configuration for the request such as headers, query parameters, and middleware options.
        """
        warn("This class is deprecated. Please use the generic RequestConfiguration class generated by the generator.", DeprecationWarning)
    

