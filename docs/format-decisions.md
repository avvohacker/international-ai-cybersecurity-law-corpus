# Format and language decisions

This note records why the corpus uses its current formats and language, and what
was considered instead. The choices favour verifiability, local reproducibility
and long-term readability over query features or presentation.

## Current formats

| Layer | Format | Why |
|---|---|---|
| Instrument records | JSON, one object per file | Schema-validatable, nested, diff-friendly, no database required |
| Candidate register | JSON array | Single reviewable register of inclusion, exclusion and pending decisions |
| Acquisition register | JSON | URL, access date, byte count and SHA-256 in one auditable file |
| Citable units | JSON Lines (`.jsonl`) | One record per line, streaming-friendly, line-level diffs, exact character and page anchors |
| Extracted text | UTF-8 plain text | Stable, tool-neutral, easy to hash and compare; no markup silently added |
| Original documents | PDF where redistributable | Preserves the official file and its internal pagination; protected standards remain links only |
| Page map | JSON | Character offsets to file pages; explicit and independent of PDF libraries |
| Schemas | JSON Schema (draft 2020-12) | Language-neutral validation contract |
| Documentation | Markdown | Readable in Git and on GitHub, no build step |
| Build outputs | JSON, Markdown, SHA-256 text | Offline, deterministic, reviewable artefacts |

## Language and tooling

The build, validation, acquisition and segmentation tools are **Python 3.12**.
Validation applies the published JSON Schema with `jsonschema`; everything else
uses the standard library. PDF extraction is a separate optional step using
`pypdf` (plus `cryptography` for the encrypted G7 PDF). `make` provides the
stable entry points.

Python was chosen because it is available in the environment, has no runtime
service to deploy, handles UTF-8 and JSON cleanly, and keeps the build auditable.
There is no JavaScript/TypeScript application, database, API or web server: the
deliverable is a corpus, not an interface.

## Alternatives considered

- **SQLite** would make joins and full-text search easier. It was not used for
  the source of truth because a binary database is harder to review in pull
  requests, obscures per-record diffs and adds a schema-migration burden. It is a
  plausible derived index later (for example a generated `corpus.db` with FTS5),
  never the only copy.
- **PostgreSQL** would support concurrent editing and richer queries, but it
  requires a service and credentials, which conflicts with the offline build.
- **CSV/TSV** is easy to inspect but poor at nested parties, sources, reservations
  and per-unit metadata; flattening would lose structure.
- **YAML** is pleasant to read but has more parsing ambiguities and is not needed:
  the records are machine-generated and validated, not hand-edited prose.
- **XML/TEI** would be strong for diplomatic transcription and scholarly
  apparatus. It was not adopted because the current texts are extracted plain
  text with page/character anchors, and TEI would add a large encoding layer
  before the corpus has a stable instrument set.
- **Akoma Ntoso / LegalDocumentML** is the main XML vocabulary for legislative
  and judicial documents. It could represent the Pact's preamble, sections,
  actions and paragraphs, and would help exchange the corpus with
  legal-information systems. It was not adopted because the canonical need here
  is exact plain-text slices with character/page anchors and JSONL units;
  encoding every instrument would add a schema and validation layer without
  improving source fidelity. A derived Akoma Ntoso export can be added later
  using the stable unit IDs, while JSON/JSONL remains canonical.
- **RDF/JSON-LD** would help link instruments, parties and legal relations across
  datasets. The current `related` and `sources` fields already expose the graph in
  a simple form; exporting JSON-LD later is straightforward and does not require
  changing the source records.
- **Git LFS** was not needed: the 14 PDFs and the China HTML page are small. It
  remains an option if the corpus grows to many large official files.
- **A static site generator** is used, but only as a deterministic renderer of
  the records: `tools/build_site.py` reads the catalogue and the stored Natural
  Earth boundaries, writes `site/index.html`, and uses no network, database,
  external font or JavaScript framework. The earlier decision not to build an
  interface was reversed when the brief asked for a consultable GitHub Pages
  public catalogue; the canonical data remain JSON/JSONL, and the site is
  not an independent source.

## Field migration, November 2026

The correction pass kept the record files as the source of truth and migrated them in place. The mapping is:

| Old field or assumption | New representation | Reason |
|---|---|---|
| `parties.signatories_total` | `parties.counts.<act>.total` plus `.verified` | One integer conflated signatures, endorsements and members |
| `parties.ratifications_total: 0` when no register was found | `counts.ratifications: {basis: "unknown", total: null, verified: 0}` | Absence of a search result is not a verified zero |
| `parties.ratifications_total: 0` for an act with no ratification | `basis: "not_applicable"`, `total: null` | “Not applicable” is not zero |
| `parties.entries[].approval` (China, WAICO) | `parties.entries[].domestic_approval` | A domestic authorisation is not international consent or a deposit |
| Implicit act type | `parties.act` (`treaty_signature`, `political_signature`, `endorsement`, `collective_issue`, `resolution`, etc.) | Different participation acts must remain distinguishable |
| Binding inferred from the document name | optional `legal_nature` with `qualification`, `rationale`, `source_ids`, required for contested form/force combinations | Qualification needs an argument and a source, not a label |
| Record-level `verification.level` as a proxy for every field | `provenance.assertions[]` with `field`, `source_ids`, `locator`, `date`, `method` | A level does not prove that status, parties, languages and provisions were each checked |
| `text.units_mode` without `pact` | schema allows `pact` | The Pact for the Future uses that segmentation |
| `dates.closed_for_signature` absent from the schema | schema allows it | WAICO records the closing date |

Existing records without `parties` were left without a parties block. Records whose status was previously inferred from an empty field were changed to `unknown` only where no official status source supported a definite value; CETS 225 remains `not_in_force` because its Treaty Office chart supplies the threshold and the count.

## Migration path

The stable `id`, `instrument_id` and `unit_id` values are the join keys. If the
corpus grows, a derived SQLite/FTS5 index or JSON-LD export can be generated from
the JSON/JSONL sources without changing the canonical records. A move to a
database would be justified by query volume or multi-user editing, not by the
current size (72 instruments and a few hundred citable units).

## What would trigger a format change

- Hundreds of thousands of units or multi-user editing: derived SQLite/Postgres
  index, with JSON/JSONL still exported.
- A need for diplomatic transcription, text variants or scholarly annotations:
  add TEI alongside the plain text, linked by the same unit IDs.
- External data exchange: publish JSON-LD or a documented CSV view generated from
  the canonical JSON, rather than replacing it.
- Legal-information interoperability: add a derived Akoma Ntoso export generated
  from `units.jsonl`, with the same IDs and source anchors; do not replace the
  canonical JSON/JSONL.
