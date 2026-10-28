"""Inactive target contracts for P4/P5; the current server does not load these."""
from __future__ import annotations

import json
import math
import uuid
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, field_validator, model_validator

from companion.profile_store import PROFILE_KINDS, validate_document

MAX_REVISION = 9_007_199_254_740_991
MAX_STORE_BYTES = 1_000_000
MAX_PROFILE_BYTES = 64_000
MAX_EXPORT_BYTES = 70_000
MAX_DRAFT_BYTES = 80_000
MAX_OPERATION_BYTES = 80_000
MAX_PROFILES = 12
MAX_WIDGETS = 60
MAX_RECEIPTS = 64
MAX_TOMBSTONES = 1024
DEFAULT_COLUMNS = 24
MAX_COLUMNS = 64
MAX_ROWS = 4096
THEMES = ('tactical-blue', 'competitive-red', 'performance-green', 'creator-purple')

Integer = Annotated[int, Field(strict=True, ge=0, le=MAX_REVISION)]
Positive = Annotated[int, Field(strict=True, ge=1, le=MAX_REVISION)]
Version = Annotated[int, Field(strict=True, ge=1, le=1)]
Identifier = Annotated[str, Field(strict=True, pattern=r'^[a-zA-Z0-9_-]{1,64}$', max_length=64)]
HexId = Annotated[str, Field(strict=True, pattern=r'^[a-f0-9]{32}$', max_length=32)]
Digest = Annotated[str, Field(strict=True, pattern=r'^[a-f0-9]{64}$', max_length=64)]
Color = Annotated[str, Field(strict=True, pattern=r'^(#[a-fA-F0-9]{6})?$', max_length=7)]
Name = Annotated[str, Field(strict=True, min_length=1, max_length=32)]
Title = Annotated[str, Field(strict=True, max_length=36)]
Theme = Literal['tactical-blue', 'competitive-red', 'performance-green', 'creator-purple']


class ContractError(ValueError):
    """Expose stable codes only, never private validation inputs."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class Widget(ClosedModel):
    id: Identifier
    kind: str = Field(json_schema_extra={'enum': sorted(PROFILE_KINDS)})
    x: Annotated[int, Field(strict=True, ge=0, lt=MAX_COLUMNS)]
    y: Annotated[int, Field(strict=True, ge=0, lt=MAX_ROWS)]
    width: Annotated[int, Field(strict=True, ge=1, le=MAX_COLUMNS)]
    height: Annotated[int, Field(strict=True, ge=1, le=MAX_ROWS)]
    variant: Literal['standard', 'compact', 'minimal']
    style: Literal['solid', 'glass', 'outline']
    title: Title
    color: Color
    background: Color
    opacity: Annotated[int, Field(strict=True, ge=60, le=100, multiple_of=5)]

    @field_validator('kind')
    @classmethod
    def known_kind(cls, value):
        if value not in PROFILE_KINDS:
            raise ValueError('widget_kind')
        return value

    @field_validator('title')
    @classmethod
    def printable_title(cls, value):
        if value != value.strip() or any(not character.isprintable() for character in value):
            raise ValueError('title')
        return value


class Layout(ClosedModel):
    columns: Annotated[int, Field(strict=True, ge=1, le=MAX_COLUMNS)]
    widgets: Annotated[list[Widget], Field(max_length=MAX_WIDGETS)]

    @model_validator(mode='after')
    def bounded_widgets(self):
        ids = [widget.id for widget in self.widgets]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate_widget_id')
        if any(widget.x + widget.width > self.columns or widget.y + widget.height > MAX_ROWS
               for widget in self.widgets):
            raise ValueError('widget_bounds')
        # Overlap is deliberately valid: collision and mobile reflow rules are not decided here.
        return self


class Appearance(ClosedModel):
    accent: Color
    background: Color
    density: Literal['normal', 'compact']


class Navigation(ClosedModel):
    mode: Literal['full', 'compact', 'hidden']
    floatingButton: bool


class Fullscreen(ClosedModel):
    showConnectionStatus: bool


class Configuration(ClosedModel):
    theme: Theme
    appearance: Appearance
    navigation: Navigation
    fullscreen: Fullscreen
    layout: Layout


class ProfileContent(ClosedModel):
    name: Name
    configuration: Configuration

    @field_validator('name')
    @classmethod
    def printable_name(cls, value):
        if value != value.strip() or any(not character.isprintable() for character in value):
            raise ValueError('name')
        return value


class Profile(ProfileContent):
    id: Identifier
    revision: Positive


class Tombstone(ClosedModel):
    id: Identifier
    revision: Positive


class Result(ClosedModel):
    kind: Literal['create', 'update', 'delete']
    profileId: Identifier
    revision: Positive
    catalogRevision: Positive


class Receipt(ClosedModel):
    operationId: HexId
    requestDigest: Digest
    result: Result


class ServerDocument(ClosedModel):
    format: Literal['ccs-dashboard-store']
    version: Version
    storeId: HexId
    catalogRevision: Positive
    profiles: Annotated[list[Profile], Field(min_length=1, max_length=MAX_PROFILES)]
    tombstones: Annotated[list[Tombstone], Field(max_length=MAX_TOMBSTONES)]
    receipts: Annotated[list[Receipt], Field(max_length=MAX_RECEIPTS)]

    @model_validator(mode='after')
    def coherent_identity(self):
        ids = [profile.id for profile in self.profiles] + [item.id for item in self.tombstones]
        operationIds = [item.operationId for item in self.receipts]
        if len(ids) != len(set(ids)) or len(operationIds) != len(set(operationIds)):
            raise ValueError('duplicate_identity')
        revisions = {item.id: item.revision for item in [*self.profiles, *self.tombstones]}
        if any(revision > self.catalogRevision for revision in revisions.values()):
            raise ValueError('revision_order')
        for receipt in self.receipts:
            result = receipt.result
            if (result.profileId not in revisions or result.revision > revisions[result.profileId]
                    or result.catalogRevision > self.catalogRevision):
                raise ValueError('receipt_reference')
        return self


class ExportDocument(ProfileContent):
    format: Literal['ccs-dashboard-export']
    version: Version


class DraftDocument(ProfileContent):
    format: Literal['ccs-dashboard-draft']
    version: Version
    storeId: HexId
    profileId: Identifier
    draftId: HexId
    baseRevision: Integer
    localRevision: Integer
    updatedAt: Integer


class OperationBase(ClosedModel):
    format: Literal['ccs-dashboard-operation']
    version: Version
    storeId: HexId
    operationId: HexId
    profileId: Identifier


class CreateOperation(OperationBase):
    kind: Literal['create']
    expectedRevision: Annotated[int, Field(strict=True, ge=0, le=0)]
    profile: ProfileContent


class UpdateOperation(OperationBase):
    kind: Literal['update']
    expectedRevision: Positive
    profile: ProfileContent


class DeleteOperation(OperationBase):
    kind: Literal['delete']
    expectedRevision: Positive


Operation = Annotated[Union[CreateOperation, UpdateOperation, DeleteOperation], Field(discriminator='kind')]
ADAPTERS = {'server': TypeAdapter(ServerDocument), 'export': TypeAdapter(ExportDocument),
            'draft': TypeAdapter(DraftDocument), 'operation': TypeAdapter(Operation)}
FORMATS = {'ccs-dashboard-' + suffix: kind for suffix, kind in
           (('store', 'server'), ('export', 'export'), ('draft', 'draft'), ('operation', 'operation'))}
LIMITS = {'server': MAX_STORE_BYTES, 'export': MAX_EXPORT_BYTES,
          'draft': MAX_DRAFT_BYTES, 'operation': MAX_OPERATION_BYTES}


def _bounded_tree(value):
    pending = [(value, 0)]
    visited = 0
    while pending:
        node, depth = pending.pop()
        visited += 1
        if depth > 24 or visited > 40000:
            raise ContractError('complexity_limit')
        if isinstance(node, float) and not math.isfinite(node):
            raise ContractError('invalid_number')
        children = node.values() if isinstance(node, dict) else node if isinstance(node, list) else ()
        pending.extend((child, depth + 1) for child in children)


def encode_document(value):
    _bounded_tree(value)
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise ContractError('invalid_document') from None


def decode_document(raw, limit=MAX_STORE_BYTES):
    if not isinstance(raw, bytes) or len(raw) > limit:
        raise ContractError('size_limit')
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ContractError('duplicate_key')
            result[key] = value
        return result
    def invalid_constant(_value):
        raise ContractError('invalid_number')
    try:
        result = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_pairs,
                            parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError):
        raise ContractError('corrupt_json') from None
    _bounded_tree(result)
    return result


def validate_contract(value, kind):
    if kind not in ADAPTERS:
        raise ContractError('unknown_contract')
    if len(encode_document(value)) > LIMITS[kind]:
        raise ContractError('size_limit')
    try:
        model = ADAPTERS[kind].validate_python(value)
        result = model.model_dump(mode='json')
    except ValidationError:
        raise ContractError('invalid_document') from None
    if kind == 'server':
        profiles = result['profiles']
    elif kind == 'operation':
        profiles = [result['profile']] if 'profile' in result else []
    else:
        profiles = [{'name': result['name'], 'configuration': result['configuration']}]
    if any(len(encode_document(profile)) > MAX_PROFILE_BYTES for profile in profiles):
        raise ContractError('profile_size_limit')
    return result


def inspect_document(raw):
    """Classify without returning private contents or untrusted error messages."""
    try:
        value = decode_document(raw)
    except ContractError as error:
        status = 'invalid' if error.code in ('size_limit', 'complexity_limit') else 'corrupt'
        return {'status': status, 'kind': None}
    if not isinstance(value, dict):
        return {'status': 'invalid', 'kind': None}
    marker = value.get('format')
    if isinstance(marker, str) and marker in FORMATS:
        kind = FORMATS[marker]
        version = value.get('version')
        if type(version) is not int or version < 1:
            return {'status': 'invalid', 'kind': kind}
        if version > 1:
            return {'status': 'future', 'kind': kind}
        try:
            validate_contract(value, kind)
        except ContractError:
            return {'status': 'invalid', 'kind': kind}
        return {'status': 'recognized', 'kind': kind}
    if marker == 'cs2-companion-layout':
        version = value.get('version')
        if type(version) is not int:
            return {'status': 'invalid', 'kind': 'export'}
        if version > 2:
            return {'status': 'future', 'kind': 'export'}
        if version != 2:
            return {'status': 'unsupported', 'kind': 'export'}
        profile = value.get('profile')
        if (len(raw) > 150000 or not isinstance(profile, dict)
                or not isinstance(profile.get('widgets'), list)
                or any(not isinstance(widget, dict) for widget in profile['widgets'])):
            return {'status': 'invalid', 'kind': 'export'}
        candidate = {**profile, 'id': 'legacy-export', 'widgets': [
            {**widget, 'id': 'legacy-' + str(index)} for index, widget in enumerate(profile['widgets'])]}
        try:
            validate_document({'profiles': [candidate], 'activeProfile': 'legacy-export'})
        except ValueError:
            return {'status': 'invalid', 'kind': 'export'}
        return {'status': 'legacy', 'kind': 'export'}
    if any(key in value for key in ('format', 'version', 'schemaVersion')):
        return {'status': 'unsupported', 'kind': None}
    try:
        validate_document(value)
        revision = value.get('revision', 0)
        if type(revision) is not int or revision < 0:
            raise ValueError('revision')
    except ValueError:
        return {'status': 'invalid', 'kind': 'server'}
    return {'status': 'legacy', 'kind': 'server'}


def contract_schema(kind):
    if kind not in ADAPTERS:
        raise ContractError('unknown_contract')
    return ADAPTERS[kind].json_schema()


def default_configuration():
    return {'theme': 'tactical-blue',
            'appearance': {'accent': '', 'background': '', 'density': 'normal'},
            'navigation': {'mode': 'compact', 'floatingButton': True},
            'fullscreen': {'showConnectionStatus': True},
            'layout': {'columns': DEFAULT_COLUMNS, 'widgets': []}}


def new_server_document():
    """Return an inactive target example, never write or activate it."""
    return validate_contract({'format': 'ccs-dashboard-store', 'version': 1,
        'storeId': uuid.uuid4().hex, 'catalogRevision': 1,
        'profiles': [{'id': 'p-default', 'name': 'My dashboard', 'revision': 1,
                      'configuration': default_configuration()}], 'tombstones': [], 'receipts': []}, 'server')
