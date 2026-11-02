"""Synthetic test composition only; the production entry point remains companion.server:app."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def run(runtime, port):
    if not (runtime / '.synthetic-publication-test').is_file():
        raise RuntimeError('Requires a disposable synthetic test directory')
    from companion import server, profile_publication
    from companion.profile_publication import PublishedProfileStore
    from companion.profile_protocol import PublishedProfileProtocol
    from fastapi.responses import HTMLResponse, Response
    import uvicorn

    server.profile_store = PublishedProfileProtocol(PublishedProfileStore(runtime / 'target/profiles.json'))
    originalSend = server.profile_store._send
    async def send(socket, message):
        if message.get('type') == 'profile_operation_ack':
            drop = runtime / 'drop-studio-ack.once'
            if drop.exists():
                drop.unlink()
                return True
            import asyncio
            for _ in range(100):
                if not (runtime / 'hold-studio-ack').exists():
                    break
                await asyncio.sleep(.1)
        return await originalSend(socket, message)
    server.profile_store._send = send
    originalWrite = profile_publication.atomic_write
    def write(path, content):
        failure = runtime / 'fail-write.once'
        if path.name == 'profiles.json' and failure.exists():
            failure.unlink()
            raise OSError('Synthetic publication write failure')
        originalWrite(path, content)
    profile_publication.atomic_write = write
    modules = ('draft-schema', 'draft-contract', 'edit-history', 'draft-publications', 'draft-store',
               'draft-session', 'published-profiles', 'profile-publication', 'dashboard-client')
    @server.app.get('/__publication_test__')
    def page():
        scripts = ''.join('<script defer src="/static/js/' + module + '.js"></script>' for module in modules)
        return HTMLResponse('<!doctype html><html><head>' + scripts
                            + '<script defer src="/__publication_harness__.js"></script></head><body>Synthetic publication test</body></html>')
    @server.app.get('/__publication_harness__.js')
    def harness():
        return Response((ROOT / 'tests/browser/publication-harness.js').read_text('utf-8'), media_type='application/javascript')
    @server.app.get('/__dashboard_test__')
    def dashboard():
        html = (ROOT / 'static/preview.html').read_text('utf-8')
        dependencies = ''.join('<script defer src="/static/js/' + module + '.js"></script>'
                               for module in ('profile-selection', 'published-profiles'))
        html = html.replace('<script defer src="/static/js/studio-preview-host.js"></script>', '')
        html = html.replace('</head>', '<link rel="stylesheet" href="/static/css/studio-density.css"></head>')
        html = html.replace('</body>', dependencies + '<script defer src="/static/js/dashboard-target.js"></script></body>')
        return HTMLResponse(html)
    @server.app.get('/__studio_test__')
    def studio():
        return HTMLResponse((ROOT / 'tests/browser/studio-preview.html').read_text('utf-8'))
    @server.app.get('/__studio_preview__')
    def studio_preview():
        return HTMLResponse((ROOT / 'static/preview.html').read_text('utf-8'))
    uvicorn.run(server.app, host='127.0.0.1', port=port, log_level='error', access_log=False,
                ws_max_size=262144, ws_max_queue=8)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('runtime', type=Path)
    parser.add_argument('port', type=int)
    args = parser.parse_args()
    run(args.runtime, args.port)
