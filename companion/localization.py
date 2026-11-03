"""Shared public JSON copy for user-facing offline maintenance tools."""
import json
from pathlib import Path
import re

LOCALES = Path(__file__).resolve().parents[1] / 'static/locales'
PARAMETERS = re.compile(r'\{([A-Za-z][A-Za-z0-9]*)\}')


class Translator:
    def __init__(self, language='EN'):
        registry = json.loads((LOCALES / 'languages.json').read_text('utf-8'))
        self.languages = {entry['code']: entry['file'] for entry in registry['languages']}
        if language not in self.languages:
            raise ValueError('unsupported_language')
        self.reference = json.loads((LOCALES / self.languages['EN']).read_text('utf-8'))
        self.catalog = json.loads((LOCALES / self.languages[language]).read_text('utf-8'))

    def text(self, key, **params):
        value = self.catalog.get(key, self.reference.get(key))
        if value is None:
            return '[' + key + ']'
        if set(PARAMETERS.findall(value)) != set(params):
            raise ValueError('locale_parameters:' + key)
        return PARAMETERS.sub(lambda match: str(params[match[1]]), value)
