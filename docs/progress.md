# Progress and remaining work

Last updated: **2026-11-23**. This file records what exists, what is only planned, and the next precise searches. Nothing below is marked complete unless it is in the repository and passes `make test`.

## Completed in this cycle

- [x] Repository inspection (README-only initial commit).
- [x] Working architecture: JSON catalog, per-instrument corpus directories, JSON Schemas, deterministic build.
- [x] Candidate register: 19 entries (1 included, 11 pending, 7 excluded).
- [x] First complete pipeline on CETS 225: official text, metadata, article units, status, checks.
- [x] Fourteen full texts stored and segmented: CETS 225; UNGA 78/241, 78/265, 78/311, 79/1, 79/62, 79/239, 79/325, 80/57 and 80/58; DEPA; SADEA; G7 Hiroshima Code; OECD AI Recommendation.
- [x] Thirteen official PDFs acquired and SHA-256 hashed; manifests generated.
- [x] EU AI Act, UNESCO Recommendation, UKSDEA, KSDPA, AfCFTA Protocol, military declaration, Bletchley/Seoul/Frontier, NATO, AU, ASEAN, five ISO/IEC standards, CETS explanatory report, EU GPAI Code.
- [x] Validator and 10 tests: schema rules, hash integrity, unit-anchor integrity, declarations cannot be binding, deterministic build.
- [x] Research log, coverage matrix, methodology and README updated to actual contents.
- [x] `build/catalog.json`, `build/CATALOG.md`, `build/checksums.sha256`.

## Not completed (explicit)

- [ ] Category 6 (drafts/negotiations) has no catalogued record.
- [ ] CETS 225 per-party table, Article 3(1)(b) declarations and reservations.
- [ ] Full CETS 225 PDF, explanatory report PDF and UNESCO PDF (access errors).
- [ ] Full EU AI Act text and consolidated amendment analysis.
- [ ] Paris AI Action Summit statement, US–UK MOU, US–EU arrangement, International AI Safety Report.
- [ ] CCW GGE on LAWS current rolling text and mandate.
- [ ] Latin America, Middle East, Central Asia regional and bilateral instruments.
- [ ] Systematic national treaty-registry search for bilateral AI clauses.
- [ ] ITU-T, IEEE and CEN-CENELEC standards.
- [ ] Non-English authentic texts and official translations.
- [ ] Party-level ratification data for DEPA, SADEA, UKSDEA, KSDPA and AfCFTA.

## Next precise searches

1. **CoE Treaty Office party data.** Fetch the chart of signatures and ratifications for CETS 225 through a JavaScript-capable browser or the underlying Treaty Office data endpoint; record every signature, ratification, reservation and Article 3(1)(b) declaration with the status date. Verify the reported Bosnia and Herzegovina ratification of 28 October 2026.
2. **CCW GGE on LAWS.** Retrieve the current GGE mandate, the latest Chair's rolling text and the 2024–2026 reports from UNODA; decide whether to catalogue a draft or a negotiation record, with document symbols and dates.
3. **Paris AI Action Summit.** Open the official Élysée/Summit statement; verify the title, date, endorsing States and the reported non-endorsements; add as a non-binding declaration if confirmed.
4. **US–UK and US–EU AI-safety instruments.** Locate the official texts (UK treaty series / State Department / European Commission); determine whether they are MOUs, administrative arrangements or political commitments; record legal status without inflating it.
5. **AfCFTA ratification.** Obtain the AU depositary record for the Digital Trade Protocol and the Annex on Emerging and Advanced Technologies; replace the secondary tralac status with a primary source and record adoption dates of the annexes.
6. **Latin America.** Search SICE/FTA and national treaty registries for AI clauses in Chile, Brazil, Mexico, Colombia, Peru, Uruguay and Mercosur/Pacific Alliance instruments; check the Chile–EU Advanced Framework Agreement and CPTPP digital chapters with a full-text keyword search.
7. **Middle East and Central Asia.** Search GCC, UAE, Saudi Arabia, Israel and Central Asian bilateral agreements for AI-specific clauses; check the Abraham Accords-adjacent digital agreements.
8. **National treaty registries.** Run systematic full-text searches for “artificial intelligence” in the U.S. TIAS, UK treaty series, Australian treaty series, Canadian treaty series, Singapore and Korean treaty databases.
9. **Standards.** Verify ITU-T Y.3172, IEEE 7000-2021 and CEN-CENELEC JTC 21 work items; add metadata-only records where access is restricted.
10. **Languages.** Acquire official French/Spanish versions of CETS 225 and the UNESCO Recommendation; never present a translation as authentic without an official-language clause.

## How to continue without starting over

1. Read `catalog/instruments/coe-cets-225.json` and `corpus/coe-cets-225/manifest.json` as the reference pattern.
2. Add a record by copying an existing JSON, changing the id/title/sources/verification, and placing any acquired file under `corpus/<id>/source/`.
3. Register the URL and hash in `catalog/acquisitions.json`; run `tools/make_manifest.py`.
4. Extract and segment only if a full text is acquired; otherwise set `text.full_text: false` and keep the original.
5. Run `make test`. Fix errors rather than suppressing them. Update `docs/coverage.md` and this file.
