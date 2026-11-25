# Corpus files

Each instrument may have a directory named after its `id`:

```text
corpus/<id>/
  source/<file>.*       acquired original (PDF, HTML); role "original" in the manifest
  text/en.txt           extracted or transcribed text; role "text"
  text/fr.txt           additional authentic text, where stored; role "text"
  pages.json            page-to-character map; role "metadata"
  pages-fr.json         page map for an additional text; role "metadata"
  units.jsonl           citable English units; role "units"
  units-fr.jsonl        citable units for an additional text; role "units"
  status/*.json         status snapshot; role "status_snapshot"
  manifest.json         hashes, sizes, roles, source URLs
```

`manifest.json` is the integrity contract checked by `make validate`. Every file listed there must exist, match its SHA-256 and size, and be unique by content. Files under `status/` are local snapshots of dynamic official pages, not official exports; the snapshot itself records its source URL and capture method. The build checks that each English unit's `text` equals the exact slice of `text/en.txt` at `char_start:char_end`, and that the unit start lies on the declared page. Additional texts, such as the French CETS 225 units, are checked by the corresponding test against their own text and page map.

## Anchors

- `char_start` / `char_end` are zero-based offsets into the UTF-8 decoded text, with `char_end` exclusive.
- `page_start` / `page_end` are **file pages** (1-based) from `pages.json`, not printed page numbers.
- CETS 225's English units use the 12 pages of the acquired official reproduction. Its French units use a 13-page sequence; `pages-fr.json` records both that sequence and the corresponding PDF page (3, 5, ..., 27).
- PDF extraction can insert spaces or line breaks. These are extraction artefacts, not textual variants; the record's `text.extraction_note` says so.

## Adding text

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-tools.txt
.venv/bin/python tools/extract_text.py <id> source/<file>.pdf
.venv/bin/python tools/extract_text.py <id> source/<file>.html --mode html \
  --html-start '<div class="content_text">' --html-end '<!-- Footer  -->'
.venv/bin/python tools/segment.py <id> --mode treaty|resolution|numbered|whole|pact
# additional text: pass --text, --pages and --output explicitly
.venv/bin/python tools/segment.py <id> --mode treaty --text text/fr.txt \
  --pages pages-fr.json --output units-fr.jsonl
.venv/bin/python tools/make_manifest.py
```

Then run `make test`. Do not edit `units.jsonl` by hand; regenerate it after changing the text.

## Rights

Originals are stored only where the known rights position permits research use. Paywalled standards are not stored. Where an original could not be acquired, only extracted text or metadata is present, and the record says so.
