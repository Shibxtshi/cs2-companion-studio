"""Disposable P7 widget gallery; never an operational server entry point."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def run(runtime, port):
    if not (runtime / '.synthetic-widget-preview').is_file():
        raise RuntimeError('Requires a disposable synthetic preview directory')
    from companion import server
    from fastapi.responses import HTMLResponse, Response
    import uvicorn
    modules = ('widgets', 'display-format', 'i18n', 'theme-preview', 'widget-presentation', 'widget-renderer')

    @server.app.get('/__widget_preview__')
    def page():
        styles = ''.join('<link rel="stylesheet" href="/static/css/' + name + '.css">'
                         for name in ('tokens', 'themes', 'styles', 'widget-presentation'))
        scripts = ''.join('<script defer src="/static/js/' + name + '.js"></script>' for name in modules)
        return HTMLResponse('<!doctype html><html lang="fr" data-theme="tactical-blue"><head>'
            + '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + '<meta name="theme-color" content="#090E14"><title>CCS — P7 representative preview</title>'
            + styles + '<link rel="stylesheet" href="/__widget_preview__.css">' + scripts
            + '<script defer src="/__widget_preview__.js"></script></head><body>'
            + '<header class="preview-head"><div class="brand"><div class="brandmark" aria-hidden="true"></div>'
            + '<div><div class="brand-name" translate="no">CCS</div><div class="sub" translate="no">MATCH CENTER / PLAYER EDITION</div></div></div>'
            + '<div class="preview-controls"><label>Language<select id="locale-select" class="select"><option value="EN">EN</option><option value="FR">FR</option></select></label>'
            + '<label>Thème d’aperçu<select id="theme-preview" class="select">'
            + '<option value="tactical-blue">Tactical Blue</option><option value="competitive-red">Competitive Red</option>'
            + '<option value="performance-green">Performance Green</option><option value="creator-purple">Creator Purple</option></select></label></div></header>'
            + '<main class="preview-main"><div class="preview-intro"><div class="preview-eyebrow">P7 / CATALOGUE DES WIDGETS</div>'
            + '<h1>Trois façons de lire la partie.</h1><p>Données synthétiques · Aperçu non enregistré · 29 widgets · 87 présentations</p>'
            + '<p class="tiny">Les détails secondaires restent accessibles. Les réserves et avertissements essentiels restent visibles.</p></div>'
            + '<div id="preview-catalog"></div></main></body></html>')

    @server.app.get('/__widget_preview__.js')
    def script():
        return Response((ROOT / 'tests/browser/widget-preview.js').read_text('utf-8'),
                        media_type='application/javascript')

    @server.app.get('/__widget_preview__.css')
    def style():
        return Response((ROOT / 'tests/browser/widget-preview.css').read_text('utf-8'),
                        media_type='text/css')

    uvicorn.run(server.app, host='127.0.0.1', port=port, access_log=False, log_level='error',
                ws_max_size=262144, ws_max_queue=8)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('runtime', type=Path)
    parser.add_argument('port', type=int)
    args = parser.parse_args()
    run(args.runtime, args.port)
