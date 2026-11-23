# Corpus files

Each instrument may have a directory named after its `id`:

```text
corpus/<id>/
  source/<file>.pdf     acquired original; role "original" in the manifest
  text/en.txt           extracted or transcribed text; role "text"
  pages.json            page-to-character map; role "metadata"
  units.jsonl           citable units; role "units"
  manifest.json         hashes, sizes, roles, source URLs
```

`manifest.json` is the integrity contract checked by `make validate`. Every file listed there must exist, match its SHA-256 and size, and be unique by content. The build also checks that each unit's `text` equals the exact slice of `text/en.txt` at `char_start:char_end`, and that the unit start lies on the declared page.

## Anchors

- `char_start` / `char_end` are zero-based offsets into the UTF-8 decoded text, with `char_end` exclusive.
- `page_start` / `page_end` are **file pages** (1-based) from `pages.json`, not printed page numbers.
- CETS 225 uses one logical page because its official PDF was not acquired (HTTP 403); its units still have exact character anchors.
- PDF extraction can insert spaces or line breaks. These are extraction artefacts, not textual variants; the record's `text.extraction_note` says so.

## Adding text

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-tools.txt
.venv/bin/python tools/extract_text.py <id> source/<file>.pdf
.venv/bin/python tools/segment.py <id> --mode treaty|resolution|numbered|whole|pact
.venv/bin/python tools/make_manifest.py
```

Then run `make test`. Do not edit `units.jsonl` by hand; regenerate it after changing the text.

## Rights

Originals are stored only where the known rights position permits research use. Paywalled standards are not stored. Where an original could not be acquired, only extracted text or metadata is present, and the record says so.
