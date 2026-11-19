from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from kiota_abstractions.serialization import AdditionalDataHolder, Parsable, ParseNode, SerializationWriter
from typing import Any, Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .session_create_request_device import SessionCreateRequest_device
    from .session_create_request_device_seed import SessionCreateRequest_device_seed
    from .session_create_request_engine import SessionCreateRequest_engine
    from .session_create_request_identity_country import SessionCreateRequest_identity_country
    from .session_create_request_profile import SessionCreateRequest_profile

@dataclass
class SessionCreateRequest(AdditionalDataHolder, Parsable):
    # Stores additional data not described in the OpenAPI description found when deserializing. Can be used for serialization as well.
    additional_data: dict[str, Any] = field(default_factory=dict)

    from .session_create_request_device import SessionCreateRequest_device

    # Device class for the population identity draw. 'random' (default) = the unchanged population draw for the requested engine. 'random_desktop' (windows/macos/linux), 'random_mobile' (ios/android), 'random_windows', 'random_android', 'random_ios' restrict WHICH real-population devices may be drawn; the weights inside the class stay the real OS/browser/device shares. When engine is omitted (or 'auto') the engine is routed from the drawn device: iOS -> webkit (always), android -> chrome, desktop -> chrome/firefox/webkit per the real browser share. An explicit engine the class cannot render on (e.g. random_ios + chrome) is rejected with 422 device_engine_mismatch, never re-routed. NOTE: an explicitly sent engine='chrome' counts as explicit even though it equals the default, so a client that always serializes engine must send 'auto' (or omit it) with random_ios / random_mobile. With identity_config/profile the operating system must lie inside the class (422 device_identity_mismatch). 'static' pins ONE fixed device: pass device_seed (the same seed always yields the same device and a byte-stable fingerprint), or a profile, or an identity_config carrying reuse_identity_seed (422 device_static_requires_seed otherwise).
    device: Optional[SessionCreateRequest_device] = SessionCreateRequest_device("random")
    from .session_create_request_engine import SessionCreateRequest_engine

    # The engine property
    engine: Optional[SessionCreateRequest_engine] = SessionCreateRequest_engine("chrome")
    # device='static' only: a stable non-negative integer, scoped to YOUR organization (the server derives the identity from org + seed, so another org's seed 1 is a different device). Seeds the population device draw AND pins the fingerprint, so every create from this org with the same seed (and engine) is the same device. Store it to bring the same device back.
    device_seed: Optional[SessionCreateRequest_device_seed] = None
    # Geo-pin for the residential exit (ISO country, e.g. 'US'). The session's timezone/geolocation follow the drawn exit's country (geo-coherence).
    identity_country: Optional[SessionCreateRequest_identity_country] = None
    # Named persistent profile. Rehydrates the saved identity bundle for this session, the same browser identity as /v1/scrape with profile=<name>.
    profile: Optional[SessionCreateRequest_profile] = None
    
    @staticmethod
    def create_from_discriminator_value(parse_node: ParseNode) -> SessionCreateRequest:
        """
        Creates a new instance of the appropriate class based on discriminator value
        param parse_node: The parse node to use to read the discriminator value and create the object
        Returns: SessionCreateRequest
        """
        if parse_node is None:
            raise TypeError("parse_node cannot be null.")
        return SessionCreateRequest()
    
    def get_field_deserializers(self,) -> dict[str, Callable[[ParseNode], None]]:
        """
        The deserialization information for the current model
        Returns: dict[str, Callable[[ParseNode], None]]
        """
        from .session_create_request_device import SessionCreateRequest_device
        from .session_create_request_device_seed import SessionCreateRequest_device_seed
        from .session_create_request_engine import SessionCreateRequest_engine
        from .session_create_request_identity_country import SessionCreateRequest_identity_country
        from .session_create_request_profile import SessionCreateRequest_profile

        from .session_create_request_device import SessionCreateRequest_device
        from .session_create_request_device_seed import SessionCreateRequest_device_seed
        from .session_create_request_engine import SessionCreateRequest_engine
        from .session_create_request_identity_country import SessionCreateRequest_identity_country
        from .session_create_request_profile import SessionCreateRequest_profile

        fields: dict[str, Callable[[Any], None]] = {
            "device": lambda n : setattr(self, 'device', n.get_enum_value(SessionCreateRequest_device)),
            "device_seed": lambda n : setattr(self, 'device_seed', n.get_object_value(SessionCreateRequest_device_seed)),
            "engine": lambda n : setattr(self, 'engine', n.get_enum_value(SessionCreateRequest_engine)),
            "identity_country": lambda n : setattr(self, 'identity_country', n.get_object_value(SessionCreateRequest_identity_country)),
            "profile": lambda n : setattr(self, 'profile', n.get_object_value(SessionCreateRequest_profile)),
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
        writer.write_enum_value("device", self.device)
        writer.write_object_value("device_seed", self.device_seed)
        writer.write_enum_value("engine", self.engine)
        writer.write_object_value("identity_country", self.identity_country)
        writer.write_object_value("profile", self.profile)
        writer.write_additional_data_value(self.additional_data)
    

