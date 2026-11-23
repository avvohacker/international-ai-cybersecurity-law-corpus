# Research log

Cycle date: **2026-11-23**. Tools used: web search, direct retrieval of official pages, the environment's URL-to-text extraction tool, `curl` for official PDFs, and local PDF text extraction. No browser automation was used.

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
| 13 | Bletchley Declaration, Seoul Declaration, Paris AI Action Summit statement | AI summit soft law | Bletchley and Seoul verified; Paris left pending (no primary text read) |
| 14 | ASEAN Guide, AU Continental AI Strategy, NATO AI Strategy | Regional and military policy | All three verified as non-binding; dates and issuers recorded |
| 15 | ISO/IEC 42001, 23894, 22989, 23053, 42006 | Technical standards | Catalogue metadata and prices verified; full texts paywalled |
| 16 | EU General-Purpose AI Code of Practice | Implementation material | Published 10 July 2025; adequacy confirmed 1 August 2025 |
| 17 | Council of Europe explanatory report CETS 225 | Interpretive material | Official report located; opening read; full text not acquired |
| 18 | ISO/IEC JTC 1/SC 42 standards catalogue | Standards coverage | Confirmed the five catalogued standards and the JTC 1/SC 42 source |

## Documents read or acquired

- CETS 225 full English text (retrieved through the extraction tool; 12 pages; transcribed).
- A/RES/78/265, 78/311, 78/241, 79/62, 79/239, 79/325, 79/1, 80/57, 80/58 (official English PDFs; 13 originals including the four agreements/codes below).
- DEPA English signing text (67 pages), SADEA (39 pages), G7 Hiroshima Code (8 pages), OECD/LEGAL/0449 booklet (12 pages).
- Official pages for UNESCO, OECD, EUR-Lex, UK Treaty Series, Singapore MTI, AU, ASEAN, NATO, ISO, GOV.UK.

## Access failures and how they are recorded

| Source | Problem | Handling |
|---|---|---|
| `rm.coe.int/1680afae3c` (CETS 225 PDF) | HTTP 403 to `curl`, including with browser user-agent; `r.jina.ai` also refused (401) | Text obtained through the environment's extraction tool; record says original PDF bytes were not acquired |
| `rm.coe.int/1680afae67` (Explanatory Report) | HTTP 403 | Metadata and opening read; full text not stored |
| UNESCO UNESDOC PDF | HTTP 403 | Metadata verified; full text not stored |
| EUR-Lex PDF endpoints | HTTP 202 with zero bytes (asynchronous/blocked) | EUR-Lex HTML/ELI pages used for metadata; no full text stored |
| CoE Treaty Office chart | JavaScript-rendered; `read_url` returned "Loading..." | Aggregate counts captured from a rendered excerpt; per-party rows not captured |
| DFAT SADEA PDF | Connection timed out once | Acquired the same treaty text from the Singapore Government Isomer copy |
| G7 PDF | Owner-password encrypted (AES) | Installed `cryptography` in the local venv; text extraction succeeded |

## Discovery versus verification

Search snippets were used to locate candidates and, in some cases, to read an official page's key statements. They were not treated as a substitute for reading a document. Records distinguish:

- full text stored and checked;
- official page/excerpt read;
- official source merely located.

The candidate register contains 11 pending items, including the Paris summit statement, US–UK and US–EU AI-safety arrangements, the International AI Safety Report, the CCW GGE on LAWS, Council of Europe Recommendation CM/Rec(2020)1, ITU-T Y.3172, IEEE 7000 and CEN-CENELEC JTC 21.

## Negative and provisional results

- No adopted treaty specifically dedicated to AI other than CETS 225 was located.
- No adopted UN framework convention specific to AI was located.
- No adopted AU or ASEAN treaty specific to AI was located; both organisations have non-binding strategies/guides.
- WTO JSI e-commerce, CPTPP, USMCA and RCEP were recorded as excluded **provisionally**, because a full-text AI keyword check was not performed. They are not claims that those agreements contain no AI reference.
- Category 6 (drafts/negotiations) remains empty in the catalogue; the CCW GGE is pending in the candidate register.
