"""Strict target publication messages, without registering a runtime endpoint."""
from typing import Literal

from pydantic import Field, model_validator
from companion.profile_contracts import (
    ClosedModel, HexId, Positive, Profile, Tombstone, Version, MAX_PROFILES, MAX_TOMBSTONES,
    ServerDocument,
)


class ProfileCatalog(ClosedModel):
    format: Literal['ccs-dashboard-catalog']
    version: Version
    storeId: HexId
    accessId: HexId
    catalogRevision: Positive
    profiles: list[Profile] = Field(min_length=1, max_length=MAX_PROFILES)
    tombstones: list[Tombstone] = Field(max_length=MAX_TOMBSTONES)

    @model_validator(mode='after')
    def coherent_catalog(self):
        ServerDocument.model_validate({
            'format': 'ccs-dashboard-store', 'version': 1, 'storeId': self.storeId,
            'catalogRevision': self.catalogRevision,
            'profiles': [profile.model_dump() for profile in self.profiles],
            'tombstones': [item.model_dump() for item in self.tombstones], 'receipts': [],
        })
        return self
