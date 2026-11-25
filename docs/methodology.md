# Methodology

Verification date for this cycle: **2026-11-24**. All access dates in records are the date the source was consulted, not the date of the legal event.

## 1. Scope and inclusion test

The catalogue separates nine layers:

1. Treaties specifically dedicated to AI.
2. Other international agreements with express, substantive AI provisions (digital, trade, bilateral).
3. Non-binding instruments: declarations, resolutions, recommendations, principles, codes.
4. Official preparatory, interpretive and implementation materials.
5. International technical standards.
6. Drafts and negotiations in progress.
7. Supranational legislation, collected separately.
8. A deliberately minimal selection of general treaties applicable to AI. It currently contains the VCLT (treaty law) and the ICCPR (human rights); it is not a general international-law inventory. The UN Charter, the UDHR, the ECHR, Convention 108+ and other general instruments are outside the corpus.
9. International cybersecurity instruments: nine cybercrime/cybersecurity treaties (Budapest, ETS 189, CETS 224, AU Malabo, UN Cybercrime, Arab Convention on IT Offences, CIS 2018, CIS 2001 and SCO 2009), three internal-law acts (NIS2, the Cyber Resilience Act and the ECOWAS Cybercrime Directive) and three non-binding instruments with official State lists (the Paris Call, the OECD Digital Security Recommendation and the Pall Mall Code). The AI and cyber counts remain separate. In the atlas's section 01 summary, **treaty-based** means an international instrument with binding form; it is not a claim that the instrument is in force. The 18 international treaty-based instruments comprise 13 in force and 5 not confirmed in force. A treaty not in force does not bind as a treaty; signatories may still be bound by the interim obligation in Article 18 VCLT not to defeat its object and purpose. The EU AI Act, NIS2, the CRA and the ECOWAS Directive are outside that set even though they are binding within their own legal orders.

An instrument enters layer 2 only if an **express AI provision** is located in the text or an official excerpt, and it is more than incidental. A trade agreement with a general digital chapter but no AI reference is recorded in the candidate register as excluded (provisionally, if a full-text keyword check was not performed).

The legal nature is determined from the instrument and its issuer, not from its title. Declarations and resolutions are `non_binding`; a joint statement is recorded as `joint_statement` rather than forced into `declaration`; voluntary company pledges are recorded as `commitment`; OECD Recommendations are non-binding legal instruments; ISO/IEC documents are voluntary technical standards; the EU AI Act, NIS2 and the Cyber Resilience Act are supranational legislation, not treaties; the ECOWAS Cybercrime Directive is regional community law, also not a treaty.

## 2. Verification levels

| Level | Meaning | This cycle |
|---|---|---:|
| `full_text_checked` | Full text stored, hashed, segmented, read; key passages asserted by tests. | 10 |
| `metadata_verified` | Official page or official excerpt read in this session; key metadata checked. | 53 |
| `source_located` | Official URL recorded; metadata from an established reference, not re-read. | 0 |

Sixteen full texts are stored, and all 16 have an acquired file registered in `catalog/acquisitions.json` (15 PDFs and one HTML). For CETS 225 the acquired PDF is a 12-page official reproduction, not the certified corrected copy, and the stored text remains a transcription. Only the ten marked `full_text_checked` were read end-to-end and are covered by key-passage tests. Six further texts are stored and segmented but remain `metadata_verified` because they were not read end-to-end. The levels are deliberately coarse and honest. `metadata_verified` is not a guarantee that every field, party or declaration was checked. Each record lists its own `verification.checks`, and `gaps` records what remains unknown.

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

`units.jsonl` stores exact `char_start`/`char_end` offsets and file-page anchors. `page_start`/`page_end` refer to the PDF file page, not necessarily the printed page number. The distinction is recorded where it matters; CETS 225 uses the 12 pages of the acquired official reproduction.

### Versions

Sources are never overwritten. If a later retrieval differs from the registered hash, `tools/acquire.py` writes the new bytes under an access-date name and exits with failure, requiring a human decision. The catalogue records versions through `dates.notes` and `related`, not through numeric filename suffixes.

## 5. Dates, status and parties

- The date of a legal event (adoption, signature, ratification, entry into force) is kept separate from the consultation date.
- Signature, ratification, acceptance, approval, accession and entry into force are separate fields.
- Reservations, declarations, objections, notifications and withdrawals are separate lists.
- A Party's position is never inferred from the position of an international organisation of which it is a member. The EU is recorded as a party to CETS 225 only because the EU deposited an instrument; EU member States are not thereby recorded as parties.
- A political declaration creates no treaty obligation, but its record must still state the act accurately. A text may be endorsed, or politically signed, or issued collectively; these are different acts and are labelled as such. `parties.act` is one of `treaty_signature`, `political_signature`, `endorsement`, `collective_issue`, `resolution`, `accession` or another recorded form. An international organisation that is a party is named outside the map frame; its member States are shown in a lighter tone only where they did not act individually.
- Counts are stored under `parties.counts`, one object per act, with `total`, `verified`, `basis` and source IDs. `basis` distinguishes `verified_total`, `declared_total`, `zero_verified`, `unknown` and `not_applicable`. A `not_applicable` count is not a zero; an `unknown` count has no total. A domestic approval (`domestic_approval`) is never counted as an international deposit.
- Field-level provenance is stored in `provenance.assertions`: field, source IDs, locator, date and method. Assertions are kept only where the locator names a real article, paragraph, page section, press release or list; generic field-name locators are removed. A record-level `verification.level` does not imply that every field was checked.
- Party names are normalized to a common English form for matching across records; the official spelling remains on the source page.
- Each map has an instrument panel built from the record: `relevance.reason`, `dates`, `dates.notes` and the record’s official sources. Its source links point only to sources marked `official_primary`, `registry` or `official_journal`; a final link opens the full record and citation. The panel does not add facts outside the record, and the heading is not repeated inside every panel.
- Where a party table could not be captured, aggregate counts are stored with the exact status date, and the missing rows are listed in `parties.unknowns`.

## 6. Rights

Each record states the known reuse position. Official texts are not automatically open-licensed. ISO/IEC standards are paywalled and only metadata and links are stored. Where a document states a reuse permission (for example the OECD booklet's free-reproduction notice, or the UK Open Government Licence), that is recorded. Where no licence was identified, the record says so.

## 7. Build and reproducibility

The build does not access the network. It uses the published JSON Schema (draft 2020-12) through `jsonschema`, with `FormatChecker` for dates and URIs, and keeps semantic checks separate from structural ones. It:

1. applies `schema/instrument.schema.json` to every record, then validates required fields, calendar dates, count bases and cross-references;
2. verifies every stored file against its manifest hash and size;
3. checks that each unit's text equals the exact slice of the primary text at its stored offsets, and that the unit start lies on the declared page;
4. checks that candidate decisions point to existing instruments when included, and do not point to catalogued instruments when excluded/pending;
5. writes `build/catalog.json`, `build/CATALOG.md`, `build/checksums.sha256` and `build/verification-report.json` with sorted keys and no timestamps;
6. optionally writes the static atlas in `site/` from the same records (`make site`), without a second data source.

The determinism test builds twice and compares the bytes. Network acquisition and PDF extraction are separate commands; their outputs are stored, so a rebuild from the repository does not depend on the network or on a PDF library. The atlas is generated from the catalogue, the stored Natural Earth boundaries and the organisation membership lists in `data/organisations.json`; it is not an independent dataset.

The link audit is a third, network-only command: `make audit-links` or `python3 tools/audit_sources.py`. It checks the official links used by the seventeen instrument panels, classifies broken links separately from anti-bot blocks and transient errors, and is deliberately excluded from `make test`.

## 8. Limits of this cycle

This is a first corpus, not a comprehensive survey. The principal limits are: two AI-specific treaties, CETS 225 not in force and WAICO's entry into force unconfirmed; five digital agreements whose AI clauses are mostly cooperative, with the AfCFTA annex using “shall” obligations for State Parties once in force; one category-6 negotiation record (CCW) but no adopted draft protocol; an inconsistent Paris Statement endorser list (60/64/65 across official publications); a unilateral Chinese initiative with no adherence list; a WAICO membership count that names 37 of 38 reported founding members, records deposits as unknown rather than zero, and treats Bangladesh's observer announcement as an application, not a membership; New Delhi's 92 itemised endorsers but a 91/92 discrepancy between the MEA and PIB lists; a BRICS statement with 11 listed member States, no individual signatures and a contested Saudi status; mostly English texts; metadata-only records for paywalled standards and for several official PDFs that returned access errors; and no systematic search of national bilateral treaty registries. These limits are stated in the coverage matrix and the progress file rather than hidden in the aggregate counts.

## 9. Sources of international law

The corpus is a register of written instruments. It covers treaties, declarations, resolutions, recommendations, codes, strategies and technical standards, plus a minimal general-treaty layer (VCLT and ICCPR). It does not systematically cover:

- customary international law, general principles of law or *jus cogens*;
- UN Security Council resolutions (no AI-specific resolution was located);
- decisions of international courts and tribunals;
- international humanitarian law (the Geneva Conventions and Additional Protocol I) and general human-rights treaties beyond the ICCPR;
- unilateral acts and national legislation, except the EU AI Act, NIS2 and the Cyber Resilience Act, which are collected as EU internal law.

These are scope limits, not findings that the sources are irrelevant. A claim about “international AI law” in this repository is a claim about the written instruments catalogued, not about the whole of international law. The audit of other candidates and the reason each was included, left pending or excluded is recorded in `catalog/candidates.json`, `docs/research-log.md` and `docs/coverage.md`.

## 10. Scope review: why two instruments were nearly missed

The first cycle exposed two near-misses: **A/HRC/RES/63/15** (6 October 2026), a dedicated AI and human-rights resolution of the Human Rights Council, and the **2025 BRICS leaders’ statement on global AI governance**. Both are now in the corpus. The reasons they were nearly missed matter more than the repairs.

### 10.1 Two different questions were being treated as one

Corpus scope answers: *is this an international AI instrument with an official text and an identifiable issuer?* Map scope answers: *is there a published State-level list of an individual legal act that can be drawn on a world map?* The first cycle sometimes used the second question to answer the first. The BRICS statement was set aside because it has no individual signature block. That is a reason not to draw eleven separate signatures; it is not a reason to leave a collective intergovernmental statement out of the corpus. The Human Rights Council resolution was set aside because the discovery path was organized around treaties, the UN General Assembly, summits and standards, and the Council was not a separate source family in the working checklist. It is an AI-specific resolution by a subsidiary organ of the UN with an official text and a recorded adoption; it belongs in the corpus even though it is non-binding and has no party list.

### 10.2 Revised inclusion rule

An instrument enters the corpus when all of the following hold:

1. It has an AI-specific object or an express, more-than-incidental AI provision.
2. Its issuer is an intergovernmental body, an international organisation, a treaty body or another authoritative standard-setter; national legislation remains outside the corpus except the EU AI Act, NIS2 and the Cyber Resilience Act as EU internal law.
3. An official text, official excerpt or official status page is available and cited.
4. The record can state the act and its legal nature without inventing a signature, ratification or party where none exists.

The legal family, the forum and the presence of an individual signature block are not inclusion tests. A collective statement, a resolution adopted without a vote and a treaty opened for signature can all qualify. The record must distinguish **listed members at a collective issue**, **endorsers**, **treaty signatories**, **political signatories**, **ratifying States**, **accessions**, **observers** and **members of an organisation** rather than forcing them into one vocabulary.

### 10.3 Maps are a view, not a gate

A record may be in the corpus without being mapped. A map requires a published State-level act: an individual signature, ratification, endorsement or a collective issue attributable to named States. When a record cannot be mapped, the reason is written in the page and in this methodology, not left implicit. The BRICS map is therefore a map of **listed member States** at a collective issue, with a distinct status and legend; it is not presented as eleven individual signatures. The New Delhi map is a map of **endorsers**; the CETS 225 map is a map of **signatures and ratifications**; the WAICO map is a map of **signatures**, not approvals. The map key and the record use the same verb.

### 10.4 Source-family watchlist and omission test

Every cycle checks the following families even when no new instrument is expected: AI-specific treaties; UN General Assembly; UN Security Council; Human Rights Council; UN system recommendations; Council of Europe; G7; G20; BRICS; the AI summit series; China-led instruments; US-led instruments; military AI (UNODA, CCW, First Committee); trade agreements with AI provisions; regional organisations (EU, AU, ASEAN, NATO and regional human-rights bodies); technical standards; multistakeholder calls; and general international law relevant to AI. A family with no qualifying instrument is recorded as a **negative result with its register and date**, not omitted from the checklist.

The omission test at the end of a cycle is deliberately mechanical:

- compare the records with the candidate register: every included candidate has a record, and every excluded or pending candidate has a written reason;
- compare the records with the source-family checklist: every family has a result, including a negative one;
- compare the records with the map list: every record with a published State-level act is either mapped or has a written map-exclusion reason;
- re-read the source families that produced the last near-misses (Human Rights Council and BRICS) before closing the cycle.

### 10.5 What this changes in practice

The corpus and the map are now reported separately in the README, the coverage matrix and the generated page. The page has seventeen maps and 63 timeline records; the difference is intentional and explained. The next review should add a standing **scope** entry to the progress file for every cycle, not only a list of new records. If a future instrument is found late, the first question is which family or test failed, not only how to add the record.
