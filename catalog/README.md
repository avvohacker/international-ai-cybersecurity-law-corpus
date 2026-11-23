# Catalogue records

One JSON file per instrument, named `<id>.json`. The filename must equal the record's `id`.

## Field guide

- `category`: one of the eight scope layers in `tools/corpuslib.py`.
- `instrument_type`: treaty, protocol, agreement, mou, joint_statement, declaration, resolution, recommendation, principles, code_of_conduct, commitment, strategy, report, guidance, standard, regulation, directive, draft, framework, terms_of_reference, decision.
- `binding_status`: `binding`, `non_binding`, `mixed`, `unknown`. A declaration or resolution cannot be `binding` (validator error).
- `status`: `in_force`, `not_in_force`, `adopted`, `open_for_signature`, `in_negotiation`, `withdrawn`, `superseded`, `unknown`.
- `relevance.reason`: why the instrument is in the corpus; `relevance.ai_provisions`: the specific provisions or parts relied on.
- `dates.verified_on`: the date the record was checked, not the date of the legal event.
- `parties`: signatures, ratifications, accessions, entry into force, reservations, declarations, objections and withdrawals. Use `unknowns` for what could not be captured.
- `languages.authentic`: authentic treaty languages only. Do not put unofficial translations here.
- `sources`: at least one official source with URL, kind, access date and a note on what was actually read.
- `rights`: known reuse position; `restricted` for paywalled standards.
- `verification.level`: `full_text_checked`, `metadata_verified` or `source_located`. The `checks` list must describe what was actually done.
- `text`: present if files are stored; `manifest` points to `corpus/<id>/manifest.json`, and `full_text` distinguishes a stored full text from an original-only record.
- `gaps`: non-empty list of what remains unknown or unverified.

See `schema/instrument.schema.json` for the machine-readable contract. The JSON Schema is documentation; the Python validator is authoritative.

## Candidate register

`candidates.json` records discovery decisions: `included`, `excluded` or `pending`, with a reason, search date and evidence. Excluded and pending candidates must not point to a catalogued instrument. An `included` candidate must point to an existing instrument id.

## Adding an instrument

1. Create `catalog/instruments/<id>.json` from an existing record.
2. Add official sources and the access date; state the verification level honestly.
3. If a full text is acquired, place the original in `corpus/<id>/source/`, register its URL and hash in `acquisitions.json`, extract and segment, then run `tools/make_manifest.py`.
4. Run `make test`.
5. Update `docs/coverage.md` and `docs/progress.md` if coverage changes.

Do not add a record with no official source. Do not mark a record `full_text_checked` unless the text is stored, segmented and tested.
