# Methodology

Verification date for this cycle: **2026-11-23**. All access dates in records are the date the source was consulted, not the date of the legal event.

## 1. Scope and inclusion test

The catalogue separates eight layers:

1. Treaties specifically dedicated to AI.
2. Other international agreements with express, substantive AI provisions (digital, trade, bilateral).
3. Non-binding instruments: declarations, resolutions, recommendations, principles, codes.
4. Official preparatory, interpretive and implementation materials.
5. International technical standards.
6. Drafts and negotiations in progress.
7. Supranational legislation, collected separately.
8. A deliberately minimal selection of general treaties applicable to AI. It currently contains the VCLT (treaty law) and the ICCPR (human rights); it is not a general international-law inventory. The UN Charter, the UDHR, the ECHR, Convention 108+ and other general instruments are outside the corpus.

An instrument enters layer 2 only if an **express AI provision** is located in the text or an official excerpt, and it is more than incidental. A trade agreement with a general digital chapter but no AI reference is recorded in the candidate register as excluded (provisionally, if a full-text keyword check was not performed).

The legal nature is determined from the instrument and its issuer, not from its title. Declarations and resolutions are `non_binding`; a joint statement is recorded as `joint_statement` rather than forced into `declaration`; voluntary company pledges are recorded as `commitment`; OECD Recommendations are non-binding legal instruments; ISO/IEC documents are voluntary technical standards; the EU AI Act is supranational legislation, not a treaty.

## 2. Verification levels

| Level | Meaning | This cycle |
|---|---|---:|
| `full_text_checked` | Full text stored, hashed, segmented, read; key passages asserted by tests. | 10 |
| `metadata_verified` | Official page or official excerpt read in this session; key metadata checked. | 34 |
| `source_located` | Official URL recorded; metadata from an established reference, not re-read. | 0 |

Sixteen full texts are stored (15 acquired originals — 14 PDFs and one HTML — plus the CETS 225 transcription); only the ten marked `full_text_checked` were read end-to-end and are covered by key-passage tests. Six further texts are stored and segmented but remain `metadata_verified` because they were not read end-to-end. The levels are deliberately coarse and honest. `metadata_verified` is not a guarantee that every field, party or declaration was checked. Each record lists its own `verification.checks`, and `gaps` records what remains unknown.

## 3. Sources and discovery

Research started from primary sources: treaty depositaries, official journals, UN document services, institutional legal pages, standards catalogues. Secondary sources were used only to discover candidates or article numbers, and the corresponding records say so. A search-result snippet is not treated as a reading of the document.

The research log records the queries actually run, the sources opened and the access failures. It does not claim exhaustive coverage.

## 4. Texts and provenance

For each acquired original:

- the file is stored under `corpus/<id>/source/`;
- its URL, access date and SHA-256 are recorded in `catalog/acquisitions.json`;
- its size and hash are repeated in `corpus/<id>/manifest.json`;
- `make validate` recomputes the hash and fails on mismatch or duplicate content.

Texts are separated into original, extracted text, metadata and citable units. `text/en.txt` is an extraction, not a diplomatic facsimile. Running headers and page numbers may be removed; wording is not corrected silently. Extraction artefacts (for example spaces inserted by PDF text extraction) are noted in the record. No missing passage is reconstructed and no machine translation is presented as authentic.

`units.jsonl` stores exact `char_start`/`char_end` offsets and file-page anchors. `page_start`/`page_end` refer to the PDF file page, not necessarily the printed page number. The distinction is recorded where it matters; CETS 225 has a single logical page because its PDF could not be acquired.

### Versions

Sources are never overwritten. If a later retrieval differs from the registered hash, `tools/acquire.py` writes the new bytes under an access-date name and exits with failure, requiring a human decision. The catalogue records versions through `dates.notes` and `related`, not through numeric filename suffixes.

## 5. Dates, status and parties

- The date of a legal event (adoption, signature, ratification, entry into force) is kept separate from the consultation date.
- Signature, ratification, acceptance, approval, accession and entry into force are separate fields.
- Reservations, declarations, objections, notifications and withdrawals are separate lists.
- A Party's position is never inferred from the position of an international organisation of which it is a member. The EU is recorded as a party to CETS 225 only because the EU deposited an instrument; EU member States are not thereby recorded as parties.
- Political declarations have no signature or ratification. Their records list endorsers in `parties.entries`; the atlas labels the act as endorsement, not signature. An international organisation that is a party is named outside the map frame; its member States are shown in a lighter tone only where they did not sign, ratify or endorse individually.
- Party names are normalized to a common English form for matching across records; the official spelling remains on the source page.
- Each map has an instrument panel built from the record: `relevance.reason`, `dates`, `dates.notes` and the record’s official sources. Its source links point only to sources marked `official_primary`, `registry` or `official_journal`; a final link opens the full record and citation. The panel does not add facts outside the record, and the heading is not repeated inside every panel.
- Where a party table could not be captured, aggregate counts are stored with the exact status date, and the missing rows are listed in `parties.unknowns`.

## 6. Rights

Each record states the known reuse position. Official texts are not automatically open-licensed. ISO/IEC standards are paywalled and only metadata and links are stored. Where a document states a reuse permission (for example the OECD booklet's free-reproduction notice, or the UK Open Government Licence), that is recorded. Where no licence was identified, the record says so.

## 7. Build and reproducibility

The build uses Python's standard library only and does not access the network. It:

1. validates required fields, enums, ISO dates and cross-references;
2. verifies every stored file against its manifest hash and size;
3. checks that each unit's text equals the exact slice of the primary text at its stored offsets, and that the unit start lies on the declared page;
4. checks that candidate decisions point to existing instruments when included, and do not point to catalogued instruments when excluded/pending;
5. writes `build/catalog.json`, `build/CATALOG.md`, `build/checksums.sha256` and `build/verification-report.json` with sorted keys and no timestamps;
6. optionally writes the static atlas in `site/` from the same records (`make site`), without a second data source.

The determinism test builds twice and compares the bytes. Network acquisition and PDF extraction are separate commands; their outputs are stored, so a rebuild from the repository does not depend on the network or on a PDF library. The atlas is generated from the catalogue, the stored Natural Earth boundaries and the organisation membership lists in `data/organisations.json`; it is not an independent dataset.

The link audit is a third, network-only command: `make audit-links` or `python3 tools/audit_sources.py`. It checks the official links used by the seven instrument panels, classifies broken links separately from anti-bot blocks and transient errors, and is deliberately excluded from `make test`.

## 8. Limits of this cycle

This is a first corpus, not a comprehensive survey. The principal limits are: two AI-specific treaties, neither in force; five digital agreements with cooperative AI clauses; one category-6 negotiation record (CCW) but no adopted draft protocol; CETS 225 and WAICO not in force; an inconsistent Paris Statement endorser list (60/64/65 across official publications); a unilateral Chinese initiative with no adherence list; a WAICO membership count that names 37 of 38 reported founding members and an observer announcement by Bangladesh that is not a membership; a New Delhi endorsement count of 92 and a BRICS statement with no itemised lists; mostly English texts; metadata-only records for paywalled standards and for several official PDFs that returned access errors; and no systematic search of national bilateral treaty registries. These limits are stated in the coverage matrix and the progress file rather than hidden in the aggregate counts.

## 9. Sources of international law

The corpus is a register of written instruments. It covers treaties, declarations, resolutions, recommendations, codes, strategies and technical standards, plus a minimal general-treaty layer (VCLT and ICCPR). It does not systematically cover:

- customary international law, general principles of law or *jus cogens*;
- UN Security Council resolutions (no AI-specific resolution was located);
- decisions of international courts and tribunals;
- international humanitarian law (the Geneva Conventions and Additional Protocol I) and general human-rights treaties beyond the ICCPR;
- unilateral acts and national legislation, except the EU AI Act.

These are scope limits, not findings that the sources are irrelevant. A claim about “international AI law” in this repository is a claim about the written instruments catalogued, not about the whole of international law. The audit of other candidates and the reason each was included, left pending or excluded is recorded in `catalog/candidates.json`, `docs/research-log.md` and `docs/coverage.md`.
