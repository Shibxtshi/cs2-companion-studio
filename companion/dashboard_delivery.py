"""Bounded dashboard fan-out; a slow peer must not stall healthy peers."""
import asyncio
from weakref import WeakKeyDictionary

_sendLocks = WeakKeyDictionary()


async def broadcast_text(clients, message, timeout=2.0):
    """Send concurrently, serializing broadcasts per peer and bounding each wait."""
    async def deliver(client):
        sendLock = _sendLocks.setdefault(client, asyncio.Lock())

        async def send():
            async with sendLock:
                await client.send_text(message)

        try:
            await asyncio.wait_for(send(), timeout)
        except Exception:
            clients.discard(client)
            try:
                await asyncio.wait_for(client.close(code=1013), 0.2)
            except Exception:
                pass

    await asyncio.gather(*(deliver(client) for client in tuple(clients)))
