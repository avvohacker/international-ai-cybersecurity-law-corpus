# Research log

Cycle date: **2026-11-23**. Tools used: web search, the Cloud browser, direct retrieval of official pages, the environment's URL-to-text extraction tool (including rendered-text extraction for official pages whose client assets returned HTTP 403), `curl` for official PDFs, and local PDF text extraction.

This log records the searches actually run and their outcome. It is not a list of every possible query.

## Queries and findings

| # | Query / target | Purpose | Outcome |
|---|---|---|---|
| 1 | Council of Europe Framework Convention artificial intelligence CETS 225 signatures ratifications | Locate the AI-specific treaty and its status | Found CETS 225; official text, Treaty Office chart, EU ratification |
| 2 | UN General Assembly resolution artificial intelligence A/RES/78/265, 79/325, 79/62 | Locate UNGA AI resolutions | Found 78/265, 78/311, 79/62, 79/239, 79/325, 80/57, 80/58 and 79/1 |
| 3 | DEPA Module 11 Emerging Trends and Technologies artificial intelligence | Test whether a digital trade agreement has an AI article | Found Article 8.2; signing text and entry-into-force dates |
| 4 | AfCFTA Digital Trade Protocol artificial intelligence article | Test African continental instrument | Found adoption 2024, emerging-technologies objective and annex; not in force |
| 5 | Political Declaration Responsible Military Use of AI and Autonomy | Military AI soft law | Found U.S. State Department page, launch date and non-binding nature |
| 6 | G7 Hiroshima Process International Code of Conduct | Advanced-AI voluntary code | Found official Japanese MIC text and Reporting Framework materials |
| 7 | OECD Recommendation Council Artificial Intelligence OECD/LEGAL/0449 | Intergovernmental AI standard | Found official Compendium record, dates, amendments, adherents |
| 8 | Singapore Australia Digital Economy Agreement artificial intelligence article | Another digital agreement with AI clause | Found Article 31 and entry into force 8 December 2020 |
| 9 | Regulation (EU) 2024/1689 EUR-Lex CELEX 32024R1689 | Supranational layer | Found ELI, OJ citation, staged application and 2026 consolidation |
| 10 | UNESCO Recommendation Ethics of AI SHS/BIO/PI/2021/1 | Universal ethics instrument | Found official page, adoption 23 November 2021, CC BY-NC-SA record |
| 11 | UK Singapore Digital Economy Agreement Article 8.61-R | Bilateral digital agreement | Found UK Treaty Series and Singapore MTI confirmation |
| 12 | Singapore Korea Digital Partnership Agreement Article 14.28 | Bilateral digital agreement | Found signed text, dates 21 November 2022 / 14 January 2023 |
| 13 | Bletchley Declaration, Seoul Declaration, Paris AI Action Summit statement | AI summit soft law | Bletchley and Seoul verified; Paris verified on the Élysée page and official PDF (65 page / 64 PDF / 60 contemporaneous release; discrepancy recorded) |
| 14 | ASEAN Guide, AU Continental AI Strategy, NATO AI Strategy | Regional and military policy | All three verified as non-binding; dates and issuers recorded |
| 15 | ISO/IEC 42001, 23894, 22989, 23053, 42006 | Technical standards | Catalogue metadata and prices verified; full texts paywalled |
| 16 | EU General-Purpose AI Code of Practice | Implementation material | Published 10 July 2025; adequacy confirmed 1 August 2025 |
| 17 | Council of Europe explanatory report CETS 225 | Interpretive material | Official report located; opening read; full text not acquired |
| 18 | ISO/IEC JTC 1/SC 42 standards catalogue | Standards coverage | Confirmed the five catalogued standards and the JTC 1/SC 42 source |
| 19 | CETS 225 Treaty Office chart and declarations page | Complete party data and Article 3(1)(b) declarations | 21 signatures, 2 ratifications (Bosnia and Herzegovina 28/10/2026; EU 15/05/2026); declarations by EU, Norway and Ukraine; no reservations/objections. No official static export was available; local JSON snapshot stored with manifest hash |
| 20 | Pact for the Future structure and AI paragraphs | Citable segmentation | 248 units and 56 actions; GDC AI-related paras. 7, 14 and 49–63; Pact paras. 48 and 51 |
| 21 | CCW GGE LAWS 2026 final report and Seventh Review Conference Decision 1 | Category-6 negotiation record | CCW/GGE.1/2026/3 (4 September 2026); mandate to elaborate an instrument; report due 2028 |
| 22 | Paris AI Action Summit statement official page and PDF | Verify the primary text, endorsers and status | Élysée page: 65 endorsers (63 States, EU, AUC); official PDF (19 February 2025): 64; contemporaneous Canadian release: 60 including South Africa, UAE and the Holy See (listed as “Vatican”); non-binding; discrepancy recorded |
| 23 | China Global AI Governance Initiative, MFA and CAC | Document the Chinese-pole instrument | Official English text and Chinese original; issued 18 October 2023; unilateral, non-binding, no adherence list; 2025 Action Plan noted as a later document, without a stated formal relationship |

## Documents read or acquired

- CETS 225 full English text (retrieved through the extraction tool; 12 pages; transcribed).
- A/RES/78/265, 78/311, 78/241, 79/62, 79/239, 79/325, 79/1, 80/57, 80/58 (official English PDFs; 15 originals including the four agreements/codes below, the Paris statement PDF and the China HTML).
- DEPA English signing text (67 pages), SADEA (39 pages), G7 Hiroshima Code (8 pages), OECD/LEGAL/0449 booklet (12 pages).
- Paris AI Action Summit statement, official Élysée PDF (3 pages, 19 February 2025) and English page; French official version consulted but not stored.
- China's Global AI Governance Initiative, official MFA English HTML (body extracted) and Chinese original on the CAC page.
- Official pages for UNESCO, OECD, EUR-Lex, UK Treaty Series, Singapore MTI, AU, ASEAN, NATO, ISO, GOV.UK.
- CETS 225 Treaty Office chart (status 23/11/2026), declarations page and EU instrument texts. The chart/declaration data is preserved in `corpus/coe-cets-225/status/coe-cets-225-status-2026-11-23.json`; this is a local snapshot, not a CoE-generated export.
- CCW/GGE.1/2026/3 final report and CCW/CONF.VII/CRP.1/Rev.3 final document of the Seventh Review Conference.

## Access failures and how they are recorded

| Source | Problem | Handling |
|---|---|---|
| `rm.coe.int/1680afae3c` (CETS 225 PDF) | HTTP 403 to `curl`, including with browser user-agent; `r.jina.ai` also refused (401) | Text obtained through the environment's extraction tool; record says original PDF bytes were not acquired |
| `rm.coe.int/1680afae67` (Explanatory Report) | HTTP 403 | Metadata and opening read; full text not stored |
| UNESCO UNESDOC PDF | HTTP 403 | Metadata verified; full text not stored |
| EUR-Lex PDF endpoints | HTTP 202 with zero bytes (asynchronous/blocked) | EUR-Lex HTML/ELI pages used for metadata; no full text stored |
| CoE Treaty Office chart | React assets returned HTTP 403 in the Cloud browser; plain `read_url` dropped the widget | Full table captured through rendered-text extraction of the official URL; status date 23/11/2026 |
| DFAT SADEA PDF | Connection timed out once | Acquired the same treaty text from the Singapore Government Isomer copy |
| G7 PDF | Owner-password encrypted (AES) | Installed `cryptography` in the local venv; text extraction succeeded |

## Discovery versus verification

Search snippets were used to locate candidates and, in some cases, to read an official page's key statements. They were not treated as a substitute for reading a document. Records distinguish:

- full text stored and checked;
- official page/excerpt read;
- official source merely located.

The candidate register contains 20 entries: 4 included (ISO/IEC 23053, the CCW GGE on LAWS, the Paris AI Action Summit Statement and China's Global AI Governance Initiative), 9 pending and 7 excluded. Pending items include the US–UK and US–EU AI-safety arrangements, the International AI Safety Report, Council of Europe Recommendation CM/Rec(2020)1, ITU-T Y.3172, IEEE 7000 and CEN-CENELEC JTC 21.

## Negative and provisional results

- No adopted treaty specifically dedicated to AI other than CETS 225 was located.
- No adopted UN framework convention specific to AI was located.
- No adopted AU or ASEAN treaty specific to AI was located; both organisations have non-binding strategies/guides.
- China's Global AI Governance Initiative is a unilateral government proposal, not an agreed international instrument; no formal adherence list was found, and the record does not attribute it to other States.
- WTO JSI e-commerce, CPTPP, USMCA and RCEP were recorded as excluded **provisionally**, because a full-text AI keyword check was not performed. They are not claims that those agreements contain no AI reference.
- Category 6 now contains one negotiation record (CCW GGE on LAWS); no adopted draft protocol or treaty text exists.
