# Contributing a translation

CCS uses shared UTF-8 JSON catalogs in the browser and Windows PowerShell 5.1 installer:

- `static/locales/en.json`: English reference.
- `static/locales/fr.json`: French.
- `ru.json`, `pl.json`, `uk.json`, `cs.json`, `ro.json`: Russian, Polish, Ukrainian, Czech and Romanian.
- `static/locales/languages.json`: available languages, native names, filenames and explicit installer confirmation letters.

## Change a sentence

Open the appropriate catalog in a UTF-8 editor. Find its descriptive key and edit only the quoted sentence. Keep the key unchanged. JSON requires double quotes; escape an embedded quote as `\"`. Do not add duplicate keys or empty translations. Save as UTF-8 without a byte-order mark.

Words such as `{amount}` and `{profile}` are named parameters. Preserve their exact spelling and braces. You may move them within the sentence. Messages and parameters are displayed as text, never executable HTML. Do not translate personal names, paths, identifiers, PINs or tokens.

## Add a language

1. Copy `en.json` to a new file, for example `xx.json`.
2. Translate every sentence. Keep all keys and parameters.
3. Add an entry to `languages.json` with a unique uppercase language code, native name and filename. Set `confirmYes` to an explicit uppercase ASCII confirmation letter displayed by the installer (RU: D for Да, UK: T for Так, PL: T for Tak, CS: A for Ano, RO: D for Da). EN/FR confirmations remain Y/O; empty input always means No. The tool displays the actual letter, so a Cyrillic keyboard layout is not required for confirmation.
4. Run `python scripts/check_locales.py`. Missing, extra, duplicate, empty or malformed entries fail validation. Fallback does not make an incomplete language complete.
5. Run `node tests/js/test_i18n.js`, then test a disposable CCS installation. Select the language, reload, and check Dashboard, Studio, preview, errors, narrow layouts and installer prompts.
6. Submit a scoped pull request describing your checks. Never include personal configuration or private screenshots.

Plural messages use suffixes such as `.one` and `.other` with a named `count`. The engine uses the language's Intl plural category, then `.other`. If another language needs additional forms, add those keys to the reference and all catalogs and validate again; no engine rewrite is necessary. Do not assemble grammar from translated fragments.

Item counts include `.few` and `.many` for Slavic languages and Romanian. Exercise 0, 1, 2, 5, 11, 21, 22 and fractional values when reviewing them. The additional catalogs were prepared with machine translation and AI-assisted terminology review; native-speaker review is welcome, particularly for long help and maintenance messages. Technical validation is not linguistic certification. The bundled Latin fonts use system fallback for Cyrillic and unsupported Latin glyphs; the application does not download remote fonts.

## Fallback and startup

English is the reference and the default for an unsupported saved preference. Unsupported selections are refused. Unknown keys are visibly bracketed, not interpreted as personal text. Lookup supports English fallback, but startup and quality checks require complete catalogs. If catalog loading fails, a minimal English recovery message is shown and the application does not start with partially translated controls.

Catalogs load before the ordered UI modules and before the body becomes visible. The existing browser language preference is preserved. Only explicit message bindings are translated; the old whole-DOM text replacement is removed.

## Writing style and glossary

Use short, natural sentences. Do not promise a save or publication before confirmation. Distinguish server connection, GSI reception and active match data. Demo values are synthetic; forecasts and bomb timing are estimates. PIN access does not encrypt LAN traffic and does not imply competitive-platform approval.

| English | French | Meaning |
|---|---|---|
| Dashboard | Dashboard | Read-only published layout |
| Customization Studio | Customization Studio | Local draft editor |
| Widget | Widget | Individual information card |
| Profile | Profil | Published configuration shared by authenticated clients |
| Draft | Brouillon | Local changes, not yet published |
| Save and apply | Enregistrer et appliquer | Explicit server publication, confirmed by acknowledgement |
| Publication | Publication | Server-confirmed configuration update |
| Preview | Prévisualisation | Local view without publication |
| Local network | Réseau local | Trusted private LAN; HTTP remains unencrypted |
| Demonstration | Démonstration | Synthetic values without private profiles |
| GSI | GSI | CS2 Game State Integration |
| PIN | PIN | Instance access code, not encryption |
| Recovery backup | Sauvegarde de récupération | Verified private recovery copy |
| Import / Export | Importer / Exporter | Reviewed transfer, never implicit publication |

Theme names and product branding stay unchanged. Catalogs contain public product copy, never credentials or personal data. Use the [contributor guide](README.md) for PR scope, documentation and licensing requirements. The offline Python translator also consumes these shared catalogs.
