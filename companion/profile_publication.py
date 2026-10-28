"""Dormant target store: one atomic published document, never a parallel active store."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import threading
import uuid

from companion.profile_contracts import ContractError, MAX_STORE_BYTES, decode_document, encode_document, validate_contract
from companion.profile_operations import apply_operation
from companion.profile_store import atomic_write


def access_id(storeId):
    """A public realm identifier derived only from the public storage generation."""
    return hashlib.sha256(('ccs-shared-pin-realm-v1:' + storeId).encode('ascii')).hexdigest()[:32]


def renewed_generation(document):
    """Pure explicit recovery/reset step; callers still owe backup and confirmation."""
    result = validate_contract(document, 'server')
    result['storeId'] = uuid.uuid4().hex
    result['receipts'] = []
    return validate_contract(result, 'server')


class PublishedProfileStore:
    """Require an explicitly provisioned target file; never initialize or convert profiles."""
    def __init__(self, path):
        self.path = Path(path).absolute()
        parents = (self.path, *self.path.parents)
        if (any(part.lower() == 'static' for part in self.path.parts)
                or any(item.is_symlink() or getattr(item, 'is_junction', lambda: False)() for item in parents)):
            raise ContractError('unsafe_storage_path')
        with self.path.open('rb') as file:
            raw = file.read(MAX_STORE_BYTES + 1)
        self._document = validate_contract(decode_document(raw), 'server')
        self._lock = threading.RLock()

    @property
    def data(self):
        return copy.deepcopy(self._document)

    def catalog(self):
        # Published documents are immutable after the committed reference swap.
        document = self._document
        return {key: copy.deepcopy(document[key]) for key in
                ('storeId', 'catalogRevision', 'profiles', 'tombstones')} | {
            'format': 'ccs-dashboard-catalog', 'version': 1,
            'accessId': access_id(document['storeId']),
        }

    def publish(self, operation):
        with self._lock:
            nextDocument, receipt = apply_operation(self._document, operation)
            if receipt['replayed']:
                return receipt
            packed = encode_document(nextDocument)
            # The backup and main replacement are separate writes. A failed main write
            # retains the published main file and memory; the backup also contains it.
            atomic_write(self.path.with_suffix(self.path.suffix + '.bak'), encode_document(self._document))
            atomic_write(self.path, packed)
            self._document = nextDocument
            return receipt
