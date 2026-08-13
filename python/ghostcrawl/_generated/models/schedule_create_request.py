from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .schedule_create_request_job_params import ScheduleCreateRequest_job_params
    from .schedule_create_request_notify_webhook import ScheduleCreateRequest_notify_webhook

@dataclass
class ScheduleCreateRequest(AdditionalDataHolder, Parsable):
    """
    POST /v1/schedules body.
    """
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    # When True, fires notify_webhook only when content hash changes.
    monitor_mode: Optional[bool] = False
    # 5-field cron expression, e.g. '0 9 * * 1'.
    cron_expr: Optional[str] = None
    # Full scrape/crawl request body.
    job_params: Optional[ScheduleCreateRequest_job_params] = None
    # 'scrape', 'crawl', or 'change_monitor'.
    job_type: Optional[str] = None
    # Schedule name. Unique per org (409 on conflict).
    name: Optional[str] = None
    # HTTPS webhook URL for change-monitor notifications.
    notify_webhook: Optional[ScheduleCreateRequest_notify_webhook] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> ScheduleCreateRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: ScheduleCreateRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return ScheduleCreateRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .schedule_create_request_job_params import ScheduleCreateRequest_job_params
        from .schedule_create_request_notify_webhook import ScheduleCreateRequest_notify_webhook

        from .schedule_create_request_job_params import ScheduleCreateRequest_job_params
        from .schedule_create_request_notify_webhook import ScheduleCreateRequest_notify_webhook

        fields: dict[str, Callable[[Any], None]] = {
            "cron_expr": lambda n : setattr(self, 'cron_expr', n.get_str_value()),
            "job_params": lambda n : setattr(self, 'job_params', n.get_object_value(ScheduleCreateRequest_job_params)),
            "job_type": lambda n : setattr(self, 'job_type', n.get_str_value()),
            "monitor_mode": lambda n : setattr(self, 'monitor_mode', n.get_bool_value()),
            "name": lambda n : setattr(self, 'name', n.get_str_value()),
            "notify_webhook": lambda n : setattr(self, 'notify_webhook', n.get_object_value(ScheduleCreateRequest_notify_webhook)),
        }
        return fields
    
    def serialize(self,writer: SerializationWriter) -> None:
        """
        Serializes information the current object
        param writer: Serialization writer to use to serialize this model
        Returns: None
        """
        if writer is None:
            raise TypeError("writer cannot be null.")
        writer.write_str_value("cron_expr", self.cron_expr)
        writer.write_object_value("job_params", self.job_params)
        writer.write_str_value("job_type", self.job_type)
        writer.write_bool_value("monitor_mode", self.monitor_mode)
        writer.write_str_value("name", self.name)
        writer.write_object_value("notify_webhook", self.notify_webhook)
        writer.write_additional_data_value(self.additional_data)
    

