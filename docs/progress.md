# Progress and remaining work

Last updated: **2026-11-25**. This file records the current state, the open gaps and the next precise searches. It is not a changelog: the chronology is in [`research-log.md`](research-log.md). Nothing is marked complete unless it is in the repository and passes `make test`.

## 1. Current state

**Counts (25 November 2026).**

| Measure | Count |
|---|---:|
| Catalogued instruments | 63 (48 AI-domain, 15 cyber-only, 0 joint) |
| Binding form | 22 (18 international + 4 internal law) |
| International in force / not confirmed | 13 / 5 |
| Non-binding | 41 |
| Full texts / records with originals | 16 / 16 (17 files) |
| State-level maps | 17 (7 treaty-based, 10 non-binding) |
| Candidate register | 37 (18 included, 9 pending, 10 excluded) |

**What the numbers mean.**

- The **48 AI-domain** records are not 48 AI treaties. They are 2 AI-specific treaties, 5 trade agreements with AI provisions, 2 general background treaties, 5 technical standards, 2 implementation texts, 1 negotiation record, 1 EU internal-law act and 30 other non-binding texts. “AI-domain” is a domain tag, not a legal category; the catalogue's `category` field is the legal partition.
- The **15 cyber-only** records are 9 cyber treaties, 3 internal-law acts (NIS2, the Cyber Resilience Act and the ECOWAS Directive) and 3 non-binding instruments (the Paris Call, OECD/LEGAL/0456 and the Pall Mall Code). No record carries both domains.
- The **18 international instruments with binding form** split 9 AI and 9 cyber. The four internal-law acts are binding in their own legal orders, not in international law. Of the 18, 13 are in force and 5 are not confirmed in force: CETS 225, WAICO, the AfCFTA Protocol, CETS 224 and the UN Cybercrime Convention.
- The **16 full texts** comprise 10 `full_text_checked` records and 6 `metadata_verified` texts; the other 47 records are metadata-only. The 16 records with an acquired original have 17 stored files; each file has a URL, access date, byte count and SHA-256 in `catalog/acquisitions.json`.

### Verified anchors

| Area | Verified position |
|---|---|
| CETS 225 | 21 signatures; 2 ratifications (Bosnia and Herzegovina 2026-10-28; European Union 2026-05-15); not in force. Five ratifications, including at least three Council of Europe member States, are required. 36 articles. A 12-page official reproduction was acquired on 2026-11-25; the direct CoE endpoint still returns HTTP 403 and the certified corrected copy was not acquired. |
| WAICO | 38 founding members reported by China's MFA, 37 individually identified. Deposits are unknown, not zero (0 individually verified); entry into force is unconfirmed. China's NPC approval of 2026-11-06 is a domestic authorisation, not a deposit. The official Chinese text was read; the English reproduction was consulted; no deposited or certified copy was acquired. |
| Budapest family | Budapest Convention: 84 Parties (48 ratifications and 36 accessions), 2 signatories, 96 reservations and 280 declaration/communication/territorial entries. ETS 189: 38 Parties. CETS 224: 52 signatures and 4 ratifications, not in force. UN Cybercrime Convention: 96 signatories, 3 Parties, not in force. AU Malabo Convention: 21 signatures, 20 Parties, in force since 2023-06-08. |
| Cyber records without current depositary tables | The Arab Convention on IT Offences, the CIS 2018 Dushanbe Agreement, the CIS 2001 Minsk Agreement and the SCO 2009 Information Security Agreement are catalogued as metadata-only. They are not mapped because a current, stable, public depositary table was not located. |
| Summit and political texts | Paris AI Action Summit: 65 endorsers on the page, 64 in the PDF and 60 in a contemporaneous release; the discrepancy is recorded. New Delhi: 92 endorsers (90 States, the EU and IFAD) on the PIB annex, 91 on the MEA page, which omits Colombia. BRICS: 11 member States listed by the presidency, no individual signatures, Saudi participation contested. Pax Silica: 26 signatories (25 States and the EU) as of 2026-10-23. |
| Other non-binding lists | Paris Call for Trust and Security in Cyberspace: 82 supporters (81 States and the EU) at source-repository commit 916433b. OECD/LEGAL/0456: 39 adherents (38 OECD members and Brazil). Pall Mall Code: 27 supporting States. |
| UN and HRC | Nine UNGA instruments, including the Pact for the Future (248 citable units across the Pact, the Global Digital Compact and the Declaration on Future Generations). A/HRC/RES/63/15 is catalogued with its follow-up panel and report still pending. The CCW GGE on LAWS is the category-6 negotiation record, with the 2026 report and the 2027–2028 mandate. |
| Trade agreements | DEPA has five Parties after Costa Rica's accession on 2026-09-17; SADEA, UKSDEA and KSDPA are in force. The AfCFTA Digital Trade Protocol is not in force; ratifications, entry into force and the annex schedules remain unknown. |
| Internal law | The EU AI Act is an AI-domain `supranational_law` record; NIS2 and the Cyber Resilience Act are cyber `supranational_law` records; the ECOWAS Cybercrime Directive is a `regional_law` record. They are binding in their legal orders but are not international treaties and are not mapped. |

### Coverage decisions

- The G20 AI Prosperity Objectives are catalogued as a non-binding ministerial deliverable; the companion AI Prosperity Compact is excluded as a private-sector pledge. The broad G20 Innovation Ministerial Statement is excluded.
- The Council of Europe Recommendation CM/Rec(2020)1 is catalogued as a non-binding recommendation.
- The Counter Ransomware Initiative, OSCE, Global Cyber Leadership Initiative and Accra Call were checked and not added: they publish a membership, an agency network or a mixed endorser group rather than a stable list of State supporters.
- The Paris Call for AI Safety and Security and the Call for Control of Frontier AI Models are not catalogued as intergovernmental instruments; the first is multi-stakeholder and open-ended.
- Collective statements are in the corpus as collective texts. They are not mapped when the issuer is a fixed membership group whose members are already listed: a map would only repeat the group's composition without adding an individual act.
- Standards are not treaties and are not treated as binding international law. The five ISO/IEC records are metadata-only.

### Atlas and reading room

The generated atlas has six sections: 00 index, 01 situation, 02 seventeen maps, 03 timeline of 63 records and 11 events, 04 reading room, 05 catalogue and 06 method. Section 01 now gives the four situation indicators, the legal-form and domain bars, and the composition of the 48 AI-domain and 15 cyber-only records. The separate three-set diagram was removed because it duplicated the catalogue's category field and was not maintainable.

The reading-room content is repository data, not Pages-only editorial text: it lives in [`data/off-the-record.json`](../data/off-the-record.json) (16 attributed entries) and is rendered by `tools/build_site.py`. The generated `site/index.html` is gitignored and rebuilt from the records and data.

### Verification infrastructure

- `catalog/instruments/*.json` is the source of truth; `units.jsonl` is generated from `text/en.txt`; manifests record every stored file with a role, size and hash.
- Page maps use inclusive `char_end`; unit anchors use half-open `char_end`. The validator checks that a unit starts inside its declared first page and that its last character (`end - 1`) is inside its declared final page. It also rejects malformed, non-contiguous or out-of-range page maps without raising.
- Field-level provenance is retained only where a specific article, paragraph, page section, press release or named list was read; generic locators are rejected by the tests.
- The 23 November 2026 catalog-wide link audit (112 official source entries in the then 45 records: 78 resolved, 26 anti-bot, 2 broken and 6 transient) is a historical measurement. It has not been rerun for the current 63-record set, and `make test` never accesses the network. The two `brics.br` URLs still do not resolve from this environment.
- `make validate` currently reports 0 errors and 1 warning: the WAICO NPC source is served over plain HTTP because the host does not complete a TLS handshake from this environment.

## 2. Gaps

**Treaty status, deposits and texts**

- CETS 225: three more ratifications, including at least two Council of Europe member States, are needed. The certified corrected copy adopted on 30 April 2025 was not acquired; corrections made after the acquired PDF's creation on 17 December 2024 are not verified. The Conference of the Parties and its rules and reporting format are not constituted.
- WAICO: the 38th founding member is unnamed; no deposited instrument was verified; entry into force is unconfirmed. Articles 5–8 provide for a Council, a Secretariat and financing, but no evidence was located that these organs have been constituted or are operating. No deposited or certified text was acquired.
- AfCFTA Digital Trade Protocol: the AU depositary ratification table, the entry-into-force notification and the Annex on Emerging and Advanced Technologies remain to be obtained.
- DEPA, SADEA, UKSDEA and KSDPA: party-level ratification and accession data remain incomplete.
- The Arab League cybercrime convention: no current dated depositary table or official update was verified. The CIS and SCO instruments remain metadata-only.

**Party lists and political texts**

- New Delhi: the reason for the 91/92 difference is not published; the MEA page may lag the PIB annex.
- BRICS: no individual signature record exists; the 11 entries are member States listed by the presidency, not signatories. The Saudi conflict is recorded, not resolved.
- Pax Silica, the AI Opportunity Statement and the San Francisco Declaration are separate deliverables; their relationship is political, not institutional.
- Paris AI Action Summit: the 65/64/60 discrepancy is recorded, not resolved.

**Pending processes**

- G7 2026 Digital and Technology Ministerial Declaration; UNGA 81 drafts `A/C.1/81/L.34` and `A/C.1/81/L.37`.
- HRC 63/15 follow-up: the 65th-session panel and the OHCHR report to the 66th session.
- CCW GGE: the 2027–2028 negotiating text and the recommendation on legal form.

**Coverage and evidence**

- ITU-T Y.3172, IEEE 7000-2021 and CEN-CENELEC JTC 21 work items.
- General international law beyond the VCLT and ICCPR (UN Charter, UDHR, ECHR, Convention 108+, IHL) is an explicit scope limit, not a claim of completeness.
- Bilateral and national treaty registries have not been systematically searched for AI clauses.
- Non-English authentic texts and official translations; CETS 225 is authentic in English and French, and the French text has not been acquired.
- The catalog-wide link audit has not been rerun for the 63-record set; the WAICO NPC plain-HTTP warning remains.

## 3. Next precise searches

1. **Transatlantic AI-safety follow-up.** Track any post-2024 renewal, terms of reference or successor to the UK–US MOU and the US–EU TTC AI-safety dialogue; check the current names and status of the UK AI Security Institute and the US Center for AI Standards and Innovation on official pages. Do not treat the 2024 records as a binding regime.
2. **WAICO follow-up.** Identify the 38th founding member from a depositary or MFA list; verify whether China or any other State has deposited an instrument of ratification, and whether the depositary has notified entry into force. Check whether the Council has admitted Bangladesh as an observer under Article 11 and whether Singapore has accepted its invitation. Decide whether to catalogue the Global AI Governance Action Plan (2025) and add only what is documented.
3. **CETS 225.** Obtain the certified corrected copy adopted on 30 April 2025 and compare it with the acquired 12-page reproduction; acquire the authentic French text. Track the three further ratifications needed for entry into force.
4. **AfCFTA.** Obtain the AU depositary ratification table for the Digital Trade Protocol, verify whether entry into force has been notified, and read the Annex on Emerging and Advanced Technologies in full.
5. **Latin America.** Search SICE/FTA and national treaty registries for AI clauses in Chile, Brazil, Mexico, Colombia, Peru, Uruguay and Mercosur/Pacific Alliance instruments; check the Chile–EU Advanced Framework Agreement and CPTPP digital chapters with a full-text keyword search.
6. **Middle East and Central Asia.** Search GCC, UAE, Saudi Arabia, Israel and Central Asian bilateral agreements for AI-specific clauses; check the Abraham Accords-adjacent digital agreements.
7. **National treaty registries.** Run systematic full-text searches for “artificial intelligence” in the U.S. TIAS, UK treaty series, Australian treaty series, Canadian treaty series, Singapore and Korean treaty databases.
8. **Standards.** Verify ITU-T Y.3172, IEEE 7000-2021 and CEN-CENELEC JTC 21 work items; add metadata-only records where access is restricted.
9. **CCW follow-up.** Track the 2027 sessions (1–5 March and 30 August–3 September 2027) and any rolling text; record the GGE's recommendation on the legal nature and specific form of the instrument, including a possible binding protocol.

## 4. How to continue without starting over

1. Read `catalog/instruments/coe-cets-225.json` and `corpus/coe-cets-225/manifest.json` as the reference pattern.
2. Add a record by copying an existing JSON, changing the id/title/sources/verification, and placing any acquired file under `corpus/<id>/source/`.
3. Register the URL and hash in `catalog/acquisitions.json`; run `tools/make_manifest.py`.
4. Extract and segment only if a full text is acquired; otherwise set `text.full_text: false` and keep the original. For A/RES/79/1 use `--mode pact`; for an official HTML page use `--mode html` and, where necessary, `--html-start`/`--html-end`.
5. Run `make test`. Fix errors rather than suppressing them. Update `docs/coverage.md` and this file.
