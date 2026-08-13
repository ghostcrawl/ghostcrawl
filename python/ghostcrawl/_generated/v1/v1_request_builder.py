from __future__ import annotations
from collections.abc import Callable
from kiota_abstractions.base_request_builder import BaseRequestBuilder
from kiota_abstractions.get_path_parameters import get_path_parameters
from kiota_abstractions.request_adapter import RequestAdapter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .agent.agent_request_builder import AgentRequestBuilder
    from .cdp.cdp_request_builder import CdpRequestBuilder
    from .content.content_request_builder import ContentRequestBuilder
    from .crawl.crawl_request_builder import CrawlRequestBuilder
    from .crawl_runs.crawl_runs_request_builder import CrawlRunsRequestBuilder
    from .datasets.datasets_request_builder import DatasetsRequestBuilder
    from .downloads.downloads_request_builder import DownloadsRequestBuilder
    from .extract.extract_request_builder import ExtractRequestBuilder
    from .kv.kv_request_builder import KvRequestBuilder
    from .map.map_request_builder import MapRequestBuilder
    from .page.page_request_builder import PageRequestBuilder
    from .pdf.pdf_request_builder import PdfRequestBuilder
    from .profiles.profiles_request_builder import ProfilesRequestBuilder
    from .recordings.recordings_request_builder import RecordingsRequestBuilder
    from .schedules.schedules_request_builder import SchedulesRequestBuilder
    from .scrape.scrape_request_builder import ScrapeRequestBuilder
    from .screenshot.screenshot_request_builder import ScreenshotRequestBuilder
    from .screenshot_blobs.screenshot_blobs_request_builder import ScreenshotBlobsRequestBuilder
    from .search.search_request_builder import SearchRequestBuilder
    from .selfhost.selfhost_request_builder import SelfhostRequestBuilder
    from .sessions.sessions_request_builder import SessionsRequestBuilder
    from .storage_states.storage_states_request_builder import StorageStatesRequestBuilder
    from .webhooks.webhooks_request_builder import WebhooksRequestBuilder

class V1RequestBuilder(BaseRequestBuilder):
    """
    Builds and executes requests for operations under /v1
    """
    def __init__(self,request_adapter: RequestAdapter, path_parameters: Union[str, dict[str, Any]]) -> None:
        """
        Instantiates a new V1RequestBuilder and sets the default values.
        param path_parameters: The raw url or the url-template parameters for the request.
        param request_adapter: The request adapter to use to execute the requests.
        Returns: None
        """
        super().__init__(request_adapter, "{+baseurl}/v1", path_parameters)
    
    @property
    def agent(self) -> AgentRequestBuilder:
        """
        The agent property
        """
        from .agent.agent_request_builder import AgentRequestBuilder

        return AgentRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def cdp(self) -> CdpRequestBuilder:
        """
        The cdp property
        """
        from .cdp.cdp_request_builder import CdpRequestBuilder

        return CdpRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def content(self) -> ContentRequestBuilder:
        """
        The content property
        """
        from .content.content_request_builder import ContentRequestBuilder

        return ContentRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def crawl(self) -> CrawlRequestBuilder:
        """
        The crawl property
        """
        from .crawl.crawl_request_builder import CrawlRequestBuilder

        return CrawlRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def crawl_runs(self) -> CrawlRunsRequestBuilder:
        """
        The crawlRuns property
        """
        from .crawl_runs.crawl_runs_request_builder import CrawlRunsRequestBuilder

        return CrawlRunsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def datasets(self) -> DatasetsRequestBuilder:
        """
        The datasets property
        """
        from .datasets.datasets_request_builder import DatasetsRequestBuilder

        return DatasetsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def downloads(self) -> DownloadsRequestBuilder:
        """
        The downloads property
        """
        from .downloads.downloads_request_builder import DownloadsRequestBuilder

        return DownloadsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def extract(self) -> ExtractRequestBuilder:
        """
        The extract property
        """
        from .extract.extract_request_builder import ExtractRequestBuilder

        return ExtractRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def kv(self) -> KvRequestBuilder:
        """
        The kv property
        """
        from .kv.kv_request_builder import KvRequestBuilder

        return KvRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def map(self) -> MapRequestBuilder:
        """
        The map property
        """
        from .map.map_request_builder import MapRequestBuilder

        return MapRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def page(self) -> PageRequestBuilder:
        """
        The page property
        """
        from .page.page_request_builder import PageRequestBuilder

        return PageRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def pdf(self) -> PdfRequestBuilder:
        """
        The pdf property
        """
        from .pdf.pdf_request_builder import PdfRequestBuilder

        return PdfRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def profiles(self) -> ProfilesRequestBuilder:
        """
        The profiles property
        """
        from .profiles.profiles_request_builder import ProfilesRequestBuilder

        return ProfilesRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def recordings(self) -> RecordingsRequestBuilder:
        """
        The recordings property
        """
        from .recordings.recordings_request_builder import RecordingsRequestBuilder

        return RecordingsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def schedules(self) -> SchedulesRequestBuilder:
        """
        The schedules property
        """
        from .schedules.schedules_request_builder import SchedulesRequestBuilder

        return SchedulesRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def scrape(self) -> ScrapeRequestBuilder:
        """
        The scrape property
        """
        from .scrape.scrape_request_builder import ScrapeRequestBuilder

        return ScrapeRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def screenshot(self) -> ScreenshotRequestBuilder:
        """
        The screenshot property
        """
        from .screenshot.screenshot_request_builder import ScreenshotRequestBuilder

        return ScreenshotRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def screenshot_blobs(self) -> ScreenshotBlobsRequestBuilder:
        """
        The screenshotBlobs property
        """
        from .screenshot_blobs.screenshot_blobs_request_builder import ScreenshotBlobsRequestBuilder

        return ScreenshotBlobsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def search(self) -> SearchRequestBuilder:
        """
        The search property
        """
        from .search.search_request_builder import SearchRequestBuilder

        return SearchRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def selfhost(self) -> SelfhostRequestBuilder:
        """
        The selfhost property
        """
        from .selfhost.selfhost_request_builder import SelfhostRequestBuilder

        return SelfhostRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def sessions(self) -> SessionsRequestBuilder:
        """
        The sessions property
        """
        from .sessions.sessions_request_builder import SessionsRequestBuilder

        return SessionsRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def storage_states(self) -> StorageStatesRequestBuilder:
        """
        The storageStates property
        """
        from .storage_states.storage_states_request_builder import StorageStatesRequestBuilder

        return StorageStatesRequestBuilder(self.request_adapter, self.path_parameters)
    
    @property
    def webhooks(self) -> WebhooksRequestBuilder:
        """
        The webhooks property
        """
        from .webhooks.webhooks_request_builder import WebhooksRequestBuilder

        return WebhooksRequestBuilder(self.request_adapter, self.path_parameters)
    

