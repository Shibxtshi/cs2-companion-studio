"""Optional synthetic publication costs; no latency threshold or personal runtime files."""
import argparse
import asyncio
import copy
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from companion.dashboard_delivery import broadcast_text
from companion.profile_contracts import encode_document, new_server_document, validate_contract
from companion.profile_operations import apply_operation
from companion.profile_publication import PublishedProfileStore


def command(document):
    profile = document['profiles'][0]
    return {'format': 'ccs-dashboard-operation', 'version': 1, 'storeId': document['storeId'],
            'operationId': uuid.uuid4().hex, 'profileId': profile['id'], 'kind': 'update',
            'expectedRevision': profile['revision'],
            'profile': {'name': 'Measured publication', 'configuration': profile['configuration']}}


def measure(callback, repeats=9):
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        callback()
        samples.append((time.perf_counter() - started) * 1000)
    return samples


async def fanout(payload, count):
    class Peer:
        async def send_text(self, text):
            assert len(text) == len(payload)
        async def close(self, code):
            pass
    peers = {Peer() for _ in range(count)}
    samples = []
    for _ in range(9):
        started = time.perf_counter()
        await broadcast_text(peers, payload)
        samples.append((time.perf_counter() - started) * 1000)
    return samples


def run():
    fixture = json.loads((ROOT / 'tests/browser/fixtures/draft-contracts.json').read_text('utf-8'))['profile']
    configuration = copy.deepcopy(fixture['configuration'])
    configuration['layout']['widgets'] = [{**copy.deepcopy(fixture['configuration']['layout']['widgets'][index % 29]),
                                            'id': 'w-' + str(index), 'y': index * 2} for index in range(60)]
    document = new_server_document()
    document['profiles'] = [{'id': 'p-' + str(index), 'name': 'Synthetic ' + str(index),
                             'revision': 1, 'configuration': copy.deepcopy(configuration)} for index in range(12)]
    document = validate_contract(document, 'server')
    emptyReceipts = measure(lambda: apply_operation(document, command(document)))
    with tempfile.TemporaryDirectory(prefix='ccs-publication-benchmark-') as directory:
        path = Path(directory) / 'profiles.json'
        path.write_bytes(encode_document(document))
        store = PublishedProfileStore(path)
        for _ in range(64):
            store.publish(command(store.data))
        full = store.data
        operation = command(full)
        results = {'profiles': 12, 'widgetsPerProfile': 60, 'receiptCount': len(full['receipts']),
                   'operationBytes': len(encode_document(operation)), 'storeBytes': len(encode_document(full)),
                   'validationMs': measure(lambda: validate_contract(full, 'server')),
                   'transitionNoReceiptsMs': emptyReceipts,
                   'transition64ReceiptsMs': measure(lambda: apply_operation(full, operation))}
        samples = []
        for _ in range(9):
            operation = command(store.data)
            started = time.perf_counter()
            store.publish(operation)
            samples.append((time.perf_counter() - started) * 1000)
        results['publicationMs'] = samples
        from companion.profile_store import atomic_write
        packed = encode_document(store.data)
        results['singleAtomicReplaceMs'] = measure(lambda: atomic_write(Path(directory) / 'atomic-probe.json', packed))
        payload = encode_document({'type': 'profiles_catalog', 'catalog': store.catalog()}).decode('utf-8')
        results['catalogBytes'] = len(payload.encode('utf-8'))
        results['inMemoryFanoutMs'] = {str(count): asyncio.run(fanout(payload, count)) for count in (1, 4, 16)}
        return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    results = run()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps({key: round(statistics.median(value), 3) if isinstance(value, list) else value
                      for key, value in results.items() if key != 'inMemoryFanoutMs'}, sort_keys=True))
    print('Fan-out scheduling uses fast in-memory peers; it is not a LAN network measurement.')
