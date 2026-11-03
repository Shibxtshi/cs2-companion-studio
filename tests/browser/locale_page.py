"""Load shared catalogs before isolated browser UI compositions, as production does."""
import re

def locale_page(html):
    if '/static/js/i18n.js' not in html:
        return html
    return re.sub(r'<script\s+defer\s+src="([^"]+)"\s*>',
        lambda match: match.group(0) if match[1].split('?')[0] == '/static/js/i18n.js' else
        '<script type="application/ccs-module" data-ccs-src="' + match[1] + '">', html)
