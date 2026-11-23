# Progress and remaining work

Last updated: **2026-11-23**. This file records what exists, what is only planned, and the next precise searches. Nothing below is marked complete unless it is in the repository and passes `make test`.

## Completed in this cycle

- [x] Repository inspection (README-only initial commit).
- [x] Working architecture: JSON catalog, per-instrument corpus directories, JSON Schemas, deterministic build.
- [x] Candidate register: 20 entries (6 included, 7 pending, 7 excluded).
- [x] First complete pipeline on CETS 225: official text, metadata, article units, status, checks.
- [x] Sixteen full texts stored and segmented: CETS 225; UNGA 78/241, 78/265, 78/311, 79/1, 79/62, 79/239, 79/325, 80/57 and 80/58; DEPA; SADEA; G7 Hiroshima Code; OECD AI Recommendation; Paris AI Action Summit Statement; China's Global AI Governance Initiative.
- [x] Fifteen originals acquired and SHA-256 hashed (14 PDFs and the China HTML); manifests generated.
- [x] CETS 225 per-party chart captured (21 signatories, 2 ratifications), Article 3(1)(b) declarations reproduced and reservations checked.
- [x] Pact for the Future segmented into 248 citable units across the Pact, Global Digital Compact and Declaration on Future Generations.
- [x] CCW GGE on LAWS catalogued as the first category-6 record, with the 2026 report and 2027–2028 negotiating mandate.
- [x] EU AI Act, UNESCO Recommendation, UKSDEA, KSDPA, AfCFTA Protocol, military declaration, Bletchley/Seoul/Frontier, NATO, AU, ASEAN, five ISO/IEC standards, CETS explanatory report, EU GPAI Code.
- [x] Paris AI Action Summit Statement verified on the official Élysée page and PDF: 65 endorsers on the page, 64 in the PDF, 60 in a contemporaneous official release; the discrepancy is recorded, not hidden.
- [x] China's Global AI Governance Initiative catalogued as the documented Chinese-pole instrument, with the official English text and the Chinese original cross-checked.
- [x] UK–US AI Safety MOU (signed 1 April 2024) catalogued from the official GOV.UK publication and press release; the full MOU was not published, so the record is metadata-only and does not infer missing clauses.
- [x] AfCFTA Digital Trade Protocol rechecked against AU primary documents: adoption, compiled annexes and the Assembly progress report. The record no longer relies on a tralac backgrounder and does not assert a ratification count without the depositary record.
- [x] ICCPR and VCLT rechecked on OHCHR and the UN Treaty Collection; the VCLT adoption date was corrected to 22 May 1969, with opening for signature on 23 May 1969.
- [x] US–EU TTC AI-safety dialogue commitment (5 April 2024) catalogued from the official European Commission and USTR joint statement and the NIST/European Commission technical-dialogue pages; recorded as a political commitment in a broader joint statement, not as an MOU or administrative arrangement.
- [x] Human-readable GitHub Pages atlas generated from the records: two maps, chronology, three-pole analysis, cross-membership matrix and filterable catalogue. The deployment workflow is ready; Pages is enabled, and a push to `main` publishes the atlas.
- [x] Validator and 17 tests: schema rules, hash integrity, unit-anchor integrity, declarations cannot be binding, Paris/China/US–UK/US–EU record checks, candidate-register counts, deterministic build.
- [x] Research log, coverage matrix, methodology and README updated to actual contents.
- [x] `build/catalog.json`, `build/CATALOG.md`, `build/checksums.sha256`.

## Not completed (explicit)

- [ ] Full CETS 225 PDF, explanatory report PDF and UNESCO PDF (access errors).
- [ ] Full EU AI Act text and consolidated amendment analysis.
- [ ] International AI Safety Report; any post-2024 renewal, terms of reference or successor to the UK–US MOU and the US–EU TTC AI-safety dialogue.
- [ ] CCW GGE 2027–2028 negotiating text and legal-form recommendation.
- [ ] General international law background beyond VCLT and ICCPR (UN Charter, UDHR, ECHR, Convention 108+); currently an explicit scope limit, not a claim of completeness.
- [ ] Systematic national treaty-registry search for bilateral AI clauses.
- [ ] ITU-T, IEEE and CEN-CENELEC standards.
- [ ] Non-English authentic texts and official translations.
- [ ] Party-level ratification data for DEPA, SADEA, UKSDEA, KSDPA and AfCFTA.

## Next precise searches

1. **Transatlantic AI-safety follow-up.** Track any post-2024 renewal, terms of reference or successor to the UK–US MOU and the US–EU TTC AI-safety dialogue; check the current names and status of the UK AI Security Institute and the US Center for AI Standards and Innovation on official pages. Do not treat the 2024 records as a binding regime.
2. **China's 2025 follow-up.** Decide whether to catalogue the Global AI Governance Action Plan (2025), whose text was read for the 2023 record, and verify the proposed World AI Cooperation Organization on official Chinese sources; determine whether either has an adherence list and add only what is documented.
3. **AfCFTA ratification and annex.** Obtain the AU depositary ratification table for the Digital Trade Protocol, verify whether entry into force has been notified, and read the Annex on Emerging and Advanced Technologies in full; record the annex provisions and any schedules.
4. **Latin America.** Search SICE/FTA and national treaty registries for AI clauses in Chile, Brazil, Mexico, Colombia, Peru, Uruguay and Mercosur/Pacific Alliance instruments; check the Chile–EU Advanced Framework Agreement and CPTPP digital chapters with a full-text keyword search.
5. **Middle East and Central Asia.** Search GCC, UAE, Saudi Arabia, Israel and Central Asian bilateral agreements for AI-specific clauses; check the Abraham Accords-adjacent digital agreements.
6. **National treaty registries.** Run systematic full-text searches for “artificial intelligence” in the U.S. TIAS, UK treaty series, Australian treaty series, Canadian treaty series, Singapore and Korean treaty databases.
7. **Standards.** Verify ITU-T Y.3172, IEEE 7000-2021 and CEN-CENELEC JTC 21 work items; add metadata-only records where access is restricted.
8. **Languages.** Acquire official French/Spanish versions of CETS 225 and the UNESCO Recommendation; never present a translation as authentic without an official-language clause.
9. **CCW follow-up.** Track the 2027 sessions (1–5 March and 30 August–3 September 2027) and any rolling text; record the GGE's recommendation on the legal nature and specific form of the instrument, including a possible binding protocol.

## How to continue without starting over

1. Read `catalog/instruments/coe-cets-225.json` and `corpus/coe-cets-225/manifest.json` as the reference pattern.
2. Add a record by copying an existing JSON, changing the id/title/sources/verification, and placing any acquired file under `corpus/<id>/source/`.
3. Register the URL and hash in `catalog/acquisitions.json`; run `tools/make_manifest.py`.
4. Extract and segment only if a full text is acquired; otherwise set `text.full_text: false` and keep the original. For A/RES/79/1 use `--mode pact`; for an official HTML page use `--mode html` and, where necessary, `--html-start`/`--html-end`.
5. Run `make test`. Fix errors rather than suppressing them. Update `docs/coverage.md` and this file.
