#!/usr/bin/env python3
"""Validate shared UTF-8 locale data and explicit production message references."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = re.compile(r'\{([A-Za-z][A-Za-z0-9]*)\}')

class LocaleError(ValueError):
    pass

def unique_object(pairs):
    result = {}
    folded = set()
    for key, value in pairs:
        if key.casefold() in folded:
            raise LocaleError('duplicate_key:' + key)
        result[key] = value
        folded.add(key.casefold())
    return result

def read_json(path):
    try:
        text = Path(path).read_bytes().decode('utf-8')
        if text.startswith('\ufeff'):
            raise LocaleError('utf8_bom_not_supported:' + str(path))
        return json.loads(text, object_pairs_hook=unique_object)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise LocaleError('invalid_utf8_or_json:' + str(path)) from error

def validate_catalog(reference, catalog):
    if not isinstance(catalog, dict) or set(reference) != set(catalog):
        raise LocaleError('catalog_keys_mismatch')
    for key, original in reference.items():
        value = catalog[key]
        if not re.fullmatch(r'[a-z][A-Za-z0-9]*(?:\.[A-Za-z0-9_]+)+', key):
            raise LocaleError('invalid_key:' + key)
        if not isinstance(value, str) or not value.strip():
            raise LocaleError('empty_or_invalid_translation:' + key)
        if set(PARAMETERS.findall(original)) != set(PARAMETERS.findall(value)):
            raise LocaleError('parameter_mismatch:' + key)
        if re.search(r'[{}]', PARAMETERS.sub('', value)):
            raise LocaleError('malformed_parameter:' + key)
        if key.endswith('.one') and key[:-4] + '.other' not in catalog:
            raise LocaleError('plural_other_missing:' + key)

def load_catalogs(folder):
    folder = Path(folder)
    registry = read_json(folder / 'languages.json')
    if registry.get('reference') != 'EN' or not isinstance(registry.get('languages'), list):
        raise LocaleError('invalid_reference_registry')
    catalogs = {}
    names = set()
    for entry in registry['languages']:
        code, filename = entry.get('code'), entry.get('file')
        if not isinstance(code, str) or not re.fullmatch(r'[A-Z][A-Z0-9-]*', code) or code in catalogs:
            raise LocaleError('invalid_or_duplicate_language')
        if not isinstance(filename, str) or not re.fullmatch(r'[a-z0-9-]+\.json', filename) or filename in names:
            raise LocaleError('invalid_or_duplicate_language_file')
        if not isinstance(entry.get('name'), str) or not entry['name'].strip():
            raise LocaleError('missing_language_name')
        if not isinstance(entry.get('confirmYes'), str) or not re.fullmatch(r'[A-Z]', entry['confirmYes']):
            raise LocaleError('invalid_confirmation_letter')
        if entry['confirmYes'] == 'N' or (code == 'EN' and entry['confirmYes'] != 'Y') or (code == 'FR' and entry['confirmYes'] != 'O'):
            raise LocaleError('unsafe_confirmation_letter')
        names.add(filename)
        catalogs[code] = read_json(folder / filename)
    if 'EN' not in catalogs:
        raise LocaleError('reference_missing')
    for catalog in catalogs.values():
        validate_catalog(catalogs['EN'], catalog)
    expected = names | {'languages.json'}
    if {path.name for path in folder.glob('*.json')} != expected:
        raise LocaleError('unregistered_catalog')
    return registry, catalogs

def references(root, catalog):
    sources = list((root / 'static/js').glob('*.js')) + list((root / 'static').glob('*.html'))
    sources += list((root / 'installer').glob('*.ps1'))
    sources += list((root / 'companion').glob('*.py'))
    sources += [root / 'tests/browser/studio-preview.html'] if (root / 'tests/browser/studio-preview.html').exists() else []
    sources += [root / 'scripts' / name for name in ('recover_profiles.py', 'generate_config.py') if (root / 'scripts' / name).exists()]
    usage = {key: [] for key in catalog}
    unknown = []
    for path in sources:
        text = path.read_text('utf-8-sig')
        staticKeys = re.findall(r"(?:CS2I18N\.(?:t|ref)|tr)\(\s*['\"]([^'\"]+)['\"]", text)
        staticKeys += re.findall(r'data-i18n(?:-[a-z-]+)?=["\x27]([a-z][A-Za-z0-9_.]+)', text)
        staticKeys += re.findall(r"['\"]((?:app|application|experience|installer|navigation|studio|widgets|maintenance|configuration)\.[A-Za-z0-9_.]+)['\"]", text)
        for candidate in staticKeys:
            if candidate.endswith('.'):
                continue
            if candidate + '.other' in catalog:
                for key in catalog:
                    if key.startswith(candidate + '.'):
                        usage[key].append(str(path.relative_to(root)))
            elif candidate not in catalog:
                unknown.append((str(path.relative_to(root)), candidate))
            else:
                usage[candidate].append(str(path.relative_to(root)))
        if path.suffix == '.ps1':
            for key in re.findall(r'\bT\s+[\x27"]([^\x27"]+)', text):
                candidate = key if '.' in key else 'installer.' + key
                if candidate not in catalog:
                    unknown.append((str(path.relative_to(root)), candidate))
                else:
                    usage[candidate].append(str(path.relative_to(root)))
        for key in catalog:
            short = key.split('.')[-1]
            if key in text or (key.count('.') == 1 and key.startswith(('experience.', 'studio.', 'navigation.')) and
                    ("'" + short + "'" in text or '"' + short + '"' in text or 'data-copy="' + short + '"' in text)):
                usage[key].append(str(path.relative_to(root)))
        if path.name == 'widgets.js':
            for key in catalog:
                if re.fullmatch(r'widgets\.[a-z_]+\.title', key):
                    usage[key].append(str(path.relative_to(root)))
    # Closed dynamic UI families have explicit finite consumers, not free-text lookup.
    dynamic = {
        'static/js/notifications.js': ['experience.notification_' + kind for kind in ('info', 'success', 'warning', 'error', 'loading', 'pending')],
        'static/js/experience.js': ['experience.setup' + str(index) + suffix for index in (1, 2, 3) for suffix in ('', 'Body')]
            + ['experience.' + kind + 'Help' for kind in ('density', 'variant', 'geometry')],
        'static/js/studio-workspace.js': ['widgets.description.' + kind for kind in re.findall(
            r'\b([a-z_]+):\{get title', (root / 'static/js/widgets.js').read_text('utf-8'))] if (root / 'static/js/widgets.js').exists() else [],
        'static/js/display-format.js': ['widgets.event.' + kind for kind in ('planted', 'defused', 'exploded')],
    }
    for consumer, keys in dynamic.items():
        if (root / consumer).exists():
            for key in keys:
                if key not in usage:
                    unknown.append((consumer, key))
                else:
                    usage[key].append(consumer)
    if unknown:
        raise LocaleError('unknown_message_references:' + repr(unknown))
    return usage

def check(root=ROOT):
    registry, catalogs = load_catalogs(Path(root) / 'static/locales')
    usage = references(Path(root), catalogs['EN'])
    unused = [key for key, paths in usage.items() if not paths]
    if unused:
        raise LocaleError('obsolete_or_unreferenced_keys:' + repr(unused))
    return {'languages': [item['code'] for item in registry['languages']],
            'keys': len(catalogs['EN']), 'usage': usage,
            'unreferencedCandidates': [key for key, paths in usage.items() if not paths]}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--coverage', type=Path)
    args = parser.parse_args()
    result = check()
    if args.coverage:
        args.coverage.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('OK: locale catalogs, key parity, UTF-8, unique keys, named parameters and production references; ' + str(result['keys']) + ' messages')

if __name__ == '__main__':
    main()
