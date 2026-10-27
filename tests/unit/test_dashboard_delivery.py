"""Deterministic fan-out tests: events establish order without timing guesses."""
import asyncio
from companion.dashboard_delivery import broadcast_text


class Peer:
    def __init__(self, hold=False, fail=False):
        self.hold = hold
        self.fail = fail
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.received = []
        self.closed = False

    async def send_text(self, message):
        self.started.set()
        if self.hold:
            await self.release.wait()
        if self.fail:
            raise OSError('synthetic peer failure')
        self.received.append(message)

    async def close(self, code):
        self.closed = code == 1013


def test_slow_peer_does_not_delay_healthy_delivery():
    async def scenario():
        slow, fast = Peer(hold=True), Peer()
        peers = {slow, fast}
        task = asyncio.create_task(broadcast_text(peers, 'state'))
        await asyncio.wait_for(fast.started.wait(), 1)
        await asyncio.wait_for(slow.started.wait(), 1)
        # Fast send completes while the slow send is deliberately still blocked.
        assert fast.received == ['state']
        assert not task.done()
        slow.release.set()
        await task
        assert len(peers) == 2
    asyncio.run(scenario())


def test_timeout_and_failure_remove_only_the_affected_peers():
    async def scenario():
        slow, bad, fast = Peer(hold=True), Peer(fail=True), Peer()
        peers = {slow, bad, fast}
        await broadcast_text(peers, 'state', timeout=0.02)
        assert peers == {fast}
        assert fast.received == ['state']
        assert slow.closed and bad.closed
    asyncio.run(scenario())


def test_concurrent_broadcasts_are_serialized_per_peer():
    async def scenario():
        peer = Peer(hold=True)
        peers = {peer}
        first = asyncio.create_task(broadcast_text(peers, 'first'))
        await peer.started.wait()
        second = asyncio.create_task(broadcast_text(peers, 'second'))
        peer.release.set()
        await asyncio.gather(first, second)
        assert peer.received == ['first', 'second']
    asyncio.run(scenario())
