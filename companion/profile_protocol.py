"""Target WebSocket adapter, instantiated only by isolated tests until activation."""
import asyncio
import re

from companion.dashboard_delivery import broadcast_text
from companion.profile_contracts import ContractError, decode_document, encode_document, validate_contract

MAX_TARGET_MESSAGE_BYTES = 81_000
MAX_TRANSFER_MESSAGE_BYTES = 150_000
MAX_EXPORT_BYTES = 70_000
OPERATION_ID = re.compile(r'^[a-f0-9]{32}$')


class PublishedProfileProtocol:
    def __init__(self, store):
        self.store = store
        self._lock = asyncio.Lock()

    @property
    def data(self):
        return self.store.data

    def snapshot(self):
        return {'type': 'profiles_catalog', 'catalog': self.store.catalog()}

    async def _send(self, socket, message):
        try:
            await asyncio.wait_for(socket.send_text(encode_document(message).decode('utf-8')), 2.0)
            return True
        except Exception:
            return False

    async def dispatch(self, raw, socket, clients):
        """Serialize target publication independently of GSI ingestion."""
        async with self._lock:
            return await self._dispatch(raw, socket, clients)

    async def _dispatch(self, raw, socket, clients):
        """Called only after the existing PIN/Origin/capacity gate."""
        try:
            encoded = raw.encode('utf-8')
            command = decode_document(encoded, MAX_TRANSFER_MESSAGE_BYTES)
            if not isinstance(command, dict):
                raise ContractError('invalid_document')
        except (ContractError, UnicodeError):
            await self._send(socket, {'type': 'profile_operation_error', 'operationId': None, 'code': 'invalid_document'})
            return True
        if command.get('type') == 'profile_import_validate':
            requestId = command.get('requestId')
            if not isinstance(requestId, str) or not OPERATION_ID.fullmatch(requestId):
                requestId = None
            try:
                if requestId is None or set(command) != {'type', 'requestId', 'document'} or not isinstance(command['document'], str):
                    raise ContractError('invalid_document')
                imported = decode_document(command['document'].encode('utf-8'), MAX_EXPORT_BYTES)
                if isinstance(imported, dict) and imported.get('format') == 'cs2-companion-layout':
                    raise ContractError('legacy_export')
                checked = validate_contract(imported, 'export')
                await self._send(socket, {'type': 'profile_import_validated', 'requestId': requestId,
                                          'content': {key: checked[key] for key in ('name', 'configuration')}})
            except (ValueError, UnicodeError) as error:
                await self._send(socket, {'type': 'profile_import_error', 'requestId': requestId,
                                          'code': error.code if isinstance(error, ContractError) else 'invalid_document'})
            return True
        if len(encoded) > MAX_TARGET_MESSAGE_BYTES:
            await self._send(socket, {'type': 'profile_operation_error', 'operationId': None, 'code': 'invalid_document'})
            return True
        if command.get('type') == 'diagnostics_request' and set(command) == {'type'}:
            return False
        if command == {'type': 'profile_catalog_request'}:
            await self._send(socket, self.snapshot())
            return True
        operationId = None
        try:
            if set(command) != {'type', 'operation'} or command['type'] != 'profile_operation':
                raise ContractError('invalid_document')
            rawOperation = command['operation']
            candidateId = rawOperation.get('operationId') if isinstance(rawOperation, dict) else None
            if isinstance(candidateId, str) and OPERATION_ID.fullmatch(candidateId):
                operationId = candidateId
            operation = validate_contract(rawOperation, 'operation')
            receipt = await asyncio.to_thread(self.store.publish, operation)
        except (ValueError, OSError) as error:
            code = error.code if isinstance(error, ContractError) else 'disk'
            await self._send(socket, {'type': 'profile_operation_error', 'operationId': operationId,
                                      'code': code, 'catalog': self.store.catalog()})
            return True
        ack = {'type': 'profile_operation_ack', 'storeId': operation['storeId'],
               'receipt': {key: value for key, value in receipt.items() if key != 'replayed'},
               'replayed': receipt['replayed']}
        delivered = await self._send(socket, ack)
        if not delivered:
            clients.discard(socket)
            try:
                await asyncio.wait_for(socket.close(code=1013), .2)
            except Exception:
                pass
        if not receipt['replayed']:
            # An acknowledgement failure must not hide a committed update from other peers.
            await broadcast_text(clients, encode_document(self.snapshot()).decode('utf-8'))
        elif delivered:
            await self._send(socket, self.snapshot())
        return True
