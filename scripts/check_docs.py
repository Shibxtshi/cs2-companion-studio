#!/usr/bin/env python3
"""Check local Markdown links without network requests or third-party packages."""
from __future__ import annotations

import argparse
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRECTORIES = {
    '.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache',
    'data', 'logs', 'cs2_cfg', '.installer-state', 'profile-reset-backups',
}
PRIVATE_FILES = {
    'AGENTS.md', 'PROJECT_CONTEXT.md', 'DECISIONS.md', 'LOCAL_WORK_PLAN.md',
    'LOCAL_AUDIT_FIX_GUIDE.md',
}


def prose(source):
    """Ignore fenced examples; they can legitimately contain illustrative links."""
    result = []
    fence = None
    for line in source.splitlines():
        match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
                fence = None
            continue
        if match:
            fence = match[1]
        else:
            result.append(line)
    return '\n'.join(result)


class HtmlReferences(HTMLParser):
    """Collect explicit HTML links, images and anchors in Markdown prose."""

    def __init__(self):
        super().__init__()
        self.targets = []
        self.anchors = set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get('id'):
            self.anchors.add(attributes['id'])
        if tag == 'a' and attributes.get('name'):
            self.anchors.add(attributes['name'])
        key = 'href' if tag == 'a' else 'src' if tag == 'img' else None
        if key and attributes.get(key):
            self.targets.append(attributes[key])


def anchors(source):
    """Support normal GitHub-style headings and explicit HTML IDs."""
    source = prose(source)
    parser = HtmlReferences()
    parser.feed(source)
    result = set(parser.anchors)
    counts = {}
    lines = source.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r'^ {0,3}#{1,6}\s+(.+?)\s*#*$', line)
        title = match[1] if match else None
        if title is None and index + 1 < len(lines) and re.fullmatch(r' {0,3}(?:=+|-+)\s*', lines[index + 1]):
            title = line.strip()
        if not title:
            continue
        title = re.sub(r'<[^>]+>', '', unescape(title)).lower()
        title = re.sub(r'[^\w\-\s]', '', title, flags=re.UNICODE)
        slug = re.sub(r'\s', '-', title)
        count = counts.get(slug, 0)
        counts[slug] = count + 1
        result.add(slug + (f'-{count}' if count else ''))
    return result


def targets(source):
    """Read inline and explicit reference links, including Markdown images."""
    source = prose(source)
    definitions = dict((match[1].strip().casefold(), match[2] or match[3]) for match in
                       re.finditer(r'^ {0,3}\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))', source, re.M))
    found = []
    for match in re.finditer(r'!?\[[^\]\n]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+["\'][^\n]*?["\'])?\s*\)', source):
        found.append(match[1] or match[2])
    for match in re.finditer(r'!?\[([^\]\n]+)\]\[([^\]\n]*)\]', source):
        label = (match[2] or match[1]).strip().casefold()
        found.append(definitions.get(label, f'UNDEFINED_REFERENCE:{label}'))
    parser = HtmlReferences()
    parser.feed(source)
    return found + parser.targets


def check(root):
    """Return checked document/link counts and actionable local errors."""
    root = root.resolve()
    documents = sorted(path for path in root.rglob('*.md')
                       if not path.is_symlink() and path.name not in PRIVATE_FILES
                       and not any(part in EXCLUDED_DIRECTORIES for part in path.relative_to(root).parts))
    errors = []
    checked = 0
    for document in documents:
        for target in targets(document.read_text(encoding='utf-8-sig')):
            if target.startswith('UNDEFINED_REFERENCE:'):
                errors.append(f'{document.relative_to(root)}: {target}')
                continue
            parsed = urlsplit(unescape(target))
            if parsed.scheme or parsed.netloc:
                continue
            checked += 1
            if not parsed.path:
                candidate = document
            elif parsed.path.startswith('/'):
                candidate = root / unquote(parsed.path).lstrip('/')
            else:
                candidate = document.parent / unquote(parsed.path)
            candidate = candidate.resolve()
            if not candidate.is_relative_to(root) or not candidate.exists():
                errors.append(f'{document.relative_to(root)}: missing/outside file {target}')
            elif parsed.fragment and candidate.suffix.lower() == '.md':
                if unquote(parsed.fragment) not in anchors(candidate.read_text(encoding='utf-8-sig')):
                    errors.append(f'{document.relative_to(root)}: missing heading {target}')
    return len(documents), checked, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    documents, links, errors = check(args.root)
    for error in errors:
        print(error)
    print(f'{documents} Markdown documents; {links} local links; {len(errors)} errors')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
