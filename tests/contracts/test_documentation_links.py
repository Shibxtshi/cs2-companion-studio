"""Exercise offline documentation checks, including non-English navigation."""
from scripts.check_docs import ROOT, anchors, check


def test_repository_documentation_links_resolve():
    documents, links, errors = check(ROOT)
    assert documents and links
    assert not errors, '\n'.join(errors)


def test_reference_images_unicode_duplicate_anchors_and_fences(tmp_path):
    (tmp_path / 'image one.png').write_bytes(b'synthetic')
    (tmp_path / 'guide.md').write_text('# Santé\n# Santé\n<a id="explicit"></a>\n', encoding='utf-8')
    (tmp_path / 'README.md').write_text(
        '[Guide](guide.md#santé-1)\n[Explicit][ref]\n'
        '[ref]: guide.md#explicit\n![Image](<image%20one.png>)\n'
        '```md\n[Example](missing.md)\n```\n', encoding='utf-8')
    assert check(tmp_path) == (2, 3, [])
    assert 'santé' in anchors('# Santé')


def test_missing_files_headings_references_and_escape_are_reported(tmp_path):
    (tmp_path / 'README.md').write_text(
        '# Home\n[Missing](missing.md)\n[Heading](#absent)\n'
        '[Ref][undefined]\n[Escape](../outside.md)\n', encoding='utf-8')
    documents, links, errors = check(tmp_path)
    assert documents == 1 and links == 3
    assert len(errors) == 4
    assert any('UNDEFINED_REFERENCE' in error for error in errors)


def test_private_context_and_runtime_markdown_are_not_read(tmp_path):
    (tmp_path / 'README.md').write_text('# Public\n', encoding='utf-8')
    (tmp_path / 'AGENTS.md').write_text('[Private](not-a-public-file)', encoding='utf-8')
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data' / 'private.md').write_text('[Private](absent)', encoding='utf-8')
    assert check(tmp_path) == (1, 0, [])
