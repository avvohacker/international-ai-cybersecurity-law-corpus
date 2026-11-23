# Progress and remaining work

Last updated: **2026-11-23**. This file records what exists, what is only planned, and the next precise searches. Nothing below is marked complete unless it is in the repository and passes `make test`.

## Completed in this cycle

- [x] Repository inspection (README-only initial commit).
- [x] Working architecture: JSON catalog, per-instrument corpus directories, JSON Schemas, deterministic build.
- [x] Candidate register: 31 entries (11 included, 11 pending, 9 excluded).
- [x] First complete pipeline on CETS 225: official text, metadata, article units, status, checks.
- [x] Sixteen full texts stored and segmented: CETS 225; UNGA 78/241, 78/265, 78/311, 79/1, 79/62, 79/239, 79/325, 80/57 and 80/58; DEPA; SADEA; G7 Hiroshima Code; OECD AI Recommendation; Paris AI Action Summit Statement; China's Global AI Governance Initiative.
- [x] Fifteen originals acquired and SHA-256 hashed (14 PDFs and the China HTML); manifests generated.
- [x] CETS 225 per-party chart captured (21 signatories, 2 ratifications), Article 3(1)(b) declarations reproduced and reservations checked.
- [x] Pact for the Future segmented into 248 citable units across the Pact, Global Digital Compact and Declaration on Future Generations.
- [x] CCW GGE on LAWS catalogued as the first category-6 record, with the 2026 report and 2027–2028 negotiating mandate.
- [x] EU AI Act, UNESCO Recommendation, UKSDEA, KSDPA, AfCFTA Protocol, military declaration, Bletchley/Seoul/Frontier, NATO, AU, ASEAN, five ISO/IEC standards, CETS explanatory report, EU GPAI Code.
- [x] Paris AI Action Summit Statement verified on the official Élysée page and PDF: 65 endorsers on the page, 64 in the PDF, 60 in a contemporaneous official release; the discrepancy is recorded, not hidden.
- [x] Party-level lists reproduced for Bletchley (29 States + EU), Seoul (10 States + EU), the military AI declaration (58 States), Pax Silica (25 States + EU) and WAICO (37 identified of 38 reported); the atlas maps eight instruments with a neutral non-participation colour, names a participating international organisation outside the map frame, and shows that organisation's member States in a lighter tone only where they did not act individually.
- [x] Organisation membership stored as machine-readable data: 27 EU member States (official EU list) and 55 African Union member States (official AU list) in `data/organisations.json`, with sources and access dates. Used only to distinguish individual acts from organisation-level participation; no instrument status is derived from it.
- [x] China's Global AI Governance Initiative catalogued as the documented Chinese-pole instrument, with the official English text and the Chinese original cross-checked.
- [x] WAICO Establishment Agreement catalogued as a treaty: 38 founding members reported by China's MFA, 37 individually identified, no deposited ratification verified, not in force (three required by Article 15); China's NPC approval of 6 November 2026 recorded without being counted as a deposit.
- [x] Pax Silica Declaration catalogued as a non-binding political declaration: 26 signatories (25 States and the EU) as of 23 October 2026, with the United States included and Taiwan recorded as a non-signatory participant; the separate AI Opportunity Statement and the 15 November 2026 San Francisco Declaration are excluded from the party count.
- [x] New Delhi AI Impact Summit Declaration (19 February 2026) added after the summit-series audit. The earlier record wrongly said no itemised list existed: the PIB annex lists 92 endorsers as of 5 March 2026 (90 States, the EU and IFAD), while the MEA page updated 21 February 2026 lists 91 and omits Colombia. The record now has 92 entries, records the discrepancy and is the eighth atlas map.
- [x] BRICS Leaders’ Statement on the Global Governance of Artificial Intelligence (6 July 2025) added after the audit of other international AI instruments. It remains a collective statement with no individual signature block, but the 11 issuing States are identified on the official BRICS page and are now recorded as issuers, not individual signatories.
- [x] WAICO observer record corrected: Bangladesh announced on 1 August 2026 that it would join 'initially as an observer', not as the 38th founding member. Article 11 requires an observer application and Council approval, and no admission is recorded. Singapore is a Pax Silica signatory reported as considering a WAICO invitation, not a member.
- [x] “02 · Three readings” rewritten from the sources: a record table, three substantive readings (regulatory models, institutional vehicles, diplomatic coalitions), a participation vocabulary and a sources note. The old three-card layout was removed.
- [x] Map headings: the short locator and the full official title now sit on the same line, and the repeated “What it is” heading was removed.
- [x] Link audit script added: `tools/audit_sources.py`, `make audit-links`, classifying broken links separately from anti-bot blocks; the classifier is tested offline and `make test` never touches the network. The 23 November 2026 run checked 26 links across eight panels: 20 resolved, 4 anti-bot (three CoE endpoints and the State Department military-AI page), 2 transient (two Australian publication pages) and 0 broken. The Indonesian founding list was moved from ekon.go.id to the Komdigi page after the audit found an incomplete TLS chain. A separate audit of the 55 external URLs in `docs/international-ai-law.md` found 41 resolved, 13 anti-bot, 1 transient and 0 broken; the report is `build/doc-link-audit.json`.
- [x] UK–US AI Safety MOU (signed 1 April 2024) catalogued from the official GOV.UK publication and press release; the full MOU was not published, so the record is metadata-only and does not infer missing clauses.
- [x] AfCFTA Digital Trade Protocol rechecked against AU primary documents: adoption, compiled annexes and the Assembly progress report. The record no longer relies on a tralac backgrounder and does not assert a ratification count without the depositary record.
- [x] ICCPR and VCLT rechecked on OHCHR and the UN Treaty Collection; the VCLT adoption date was corrected to 22 May 1969, with opening for signature on 23 May 1969.
- [x] US–EU TTC AI-safety dialogue commitment (5 April 2024) catalogued from the official European Commission and USTR joint statement and the NIST/European Commission technical-dialogue pages; recorded as a political commitment in a broader joint statement, not as an MOU or administrative arrangement.
- [x] Human-readable GitHub Pages atlas generated from the records: eight maps, each with the recorded parties grouped by act, the instrument's official title on the same line as its short locator, and an instrument panel giving description, dates, history and official-source links; a chronology; an analytical section that reads the “three poles” image against the legal record; and a filterable catalogue. The deployment workflow is ready; Pages is enabled, and a push to `main` publishes the atlas.
- [x] Validator and 35 tests: schema rules, hash integrity, unit-anchor integrity, declarations cannot be binding, Paris/China/US–UK/US–EU/WAICO/Pax Silica/New Delhi/BRICS/HRC record checks, party lists for Bletchley/Seoul/military AI, candidate-register counts, map completeness and neutrality, map order by binding status and adopter count, organisation membership resolution, party-list-to-record consistency, instrument-panel content and source citations checked against records, numeric claims derived from records, historical notes checked against records, offline link-audit classification, and deterministic build.
- [x] Source-family coverage checklist created in `docs/coverage-checklist.md`, with canonical registers, check dates, results and decisions. It found the HRC resolution, corrected the New Delhi and BRICS party records, identified three pending processes (G7 2026, G20 AI Compact/Objectives and UNGA 81 drafts) and documented two exclusions (Paris Call and the broad G20 Innovation Ministerial Statement).
- [x] WAICO depositary recheck (23 November 2026): Article 18 designates the Government of China as depositary; no public depositary register, status table or notification of a deposited Chinese instrument was located. The record retains 38 reported founding members, 37 identified and 0 deposited ratifications. The map therefore remains a signature map.
- [x] Research log, coverage matrix, methodology and README updated to actual contents.
- [x] `build/catalog.json`, `build/CATALOG.md`, `build/checksums.sha256`.

## Not completed (explicit)

- [ ] WAICO depositary confirmation: the 38th founding member and the deposit of China's instrument of ratification. The Government of China is the depositary under Article 18; the 9 November 2026 MFA statement reports 38 founding members but does not name the 38th, and no public depositary register or notification was located. Bangladesh is an observer applicant under Article 11, not the 38th member; no Council admission is recorded. Singapore's invitation remains under consideration.
- [ ] Full CETS 225 PDF, explanatory report PDF and UNESCO PDF (access errors).
- [ ] Full EU AI Act text and consolidated amendment analysis.
- [ ] International AI Safety Report; any post-2024 renewal, terms of reference or successor to the UK–US MOU and the US–EU TTC AI-safety dialogue.
- [ ] HRC 63/15 follow-up: the panel discussion at the 65th session and the OHCHR report to the 66th session.
- [ ] G7 2026 Digital and Technology Ministerial Declaration; G20 AI Prosperity Compact and AI Prosperity Objectives; UNGA 81 drafts L.34/L.37. These are pending candidates, not adopted instruments.
- [ ] New Delhi 91/92 discrepancy: check whether the MEA page is updated or whether Colombia's endorsement is separately documented.
- [ ] CCW GGE 2027–2028 negotiating text and legal-form recommendation.
- [ ] General international law background beyond VCLT and ICCPR (UN Charter, UDHR, ECHR, Convention 108+); currently an explicit scope limit, not a claim of completeness.
- [ ] Systematic national treaty-registry search for bilateral AI clauses.
- [ ] ITU-T, IEEE and CEN-CENELEC standards.
- [ ] Non-English authentic texts and official translations.
- [ ] Party-level ratification data for DEPA, SADEA, UKSDEA, KSDPA and AfCFTA.

## Next precise searches

1. **Transatlantic AI-safety follow-up.** Track any post-2024 renewal, terms of reference or successor to the UK–US MOU and the US–EU TTC AI-safety dialogue; check the current names and status of the UK AI Security Institute and the US Center for AI Standards and Innovation on official pages. Do not treat the 2024 records as a binding regime.
2. **WAICO follow-up.** Identify the 38th founding member from a depositary or MFA list; verify whether China or any other State has deposited an instrument of ratification, and whether the depositary has notified entry into force. Check whether the Council has admitted Bangladesh as an observer under Article 11 and whether Singapore has accepted its invitation. Also decide whether to catalogue the Global AI Governance Action Plan (2025), whose text was read for the 2023 record, and add only what is documented.
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
