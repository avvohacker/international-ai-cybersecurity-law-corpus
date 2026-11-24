# Cybersecurity integration plan

**Status:** Phase 2 complete for the Budapest family; the UN Cybercrime and AU Malabo Conventions and the Arab, CIS and SCO treaties have been added. The corpus is a joint **AI and international cybersecurity law** corpus with fifteen cybersecurity-only records: nine treaties — the Budapest Convention (ETS 185, 84 itemised Parties), ETS 189 (38 Parties), CETS 224 (52 signatories, not in force), the AU Malabo Convention (21 signatures, 20 Parties, in force since 2023), the UN Cybercrime Convention (96 signatories including the EU, three Parties, not in force), the Arab Convention on IT Offences (in force, current party table unavailable), the CIS 2018 Dushanbe Agreement (seven declared Parties), the CIS 2001 Minsk Agreement (in force, current party table unavailable) and the SCO 2009 Information Security Agreement (in force, current party table unavailable) — plus three internal-law acts (NIS2, the Cyber Resilience Act and the ECOWAS Cybercrime Directive) and three non-binding instruments: the Paris Call, the OECD Recommendation on Digital Security of Critical Activities (39 adherents) and the Pall Mall Code of Practice for States (27 supporting States). The five treaties with stable itemised depositary tables are mapped; the Arab, CIS and SCO treaties are metadata-only and unmapped; the three non-binding texts are mapped from their official State lists; internal law is catalogued without boxes or maps. The AI layer is 48 records; the total is 63. Phase 4 (norms, standards and channels) remains partial.

## 1. Why cybersecurity is a second domain, not a filter

Cybersecurity law is not merely context for AI law. It governs the infrastructure, products, networks and criminal-law cooperation on which AI systems depend, and it often supplies the operative security duties that AI-specific texts leave open. The EU AI Act's cybersecurity requirements, the Cyber Resilience Act, NIS2 supply-chain duties and CETS 225's risk-management duties are obvious overlaps; the Budapest Convention and the UN Cybercrime Convention regulate the criminal-procedure layer that AI investigations already use.

The earlier proposal limited cyber records to instruments with an express AI hook. That was too narrow. The corpus should admit the international cybersecurity layer in its own right, while keeping the AI and cyber counts separate and visible.

The purpose is now:

> Record the international and regional instruments that govern cybersecurity, mark their relationship to AI where one exists, and show which parts of the cyber layer are binding, in force and operational.

## 2. Scope rule

A cybersecurity record enters the catalogue if it is one of the following:

1. an international treaty, convention, protocol or agreement on cybercrime, critical-infrastructure protection, information security, cyber operations or cross-border cyber cooperation;
2. regional law that directly regulates cybersecurity and has cross-border or regulatory effect (EU NIS2, the Cyber Resilience Act, and comparable regional instruments);
3. an intergovernmental political commitment or agreed norm on responsible State behaviour in cyberspace, marked non-binding;
4. an international technical standard with a cybersecurity governance or assurance scope (for example ISO/IEC 27001 and 27002, IEC 62443), marked as a standard rather than as law;
5. a bilateral or multilateral cyber cooperation agreement that creates a channel, an obligation or a shared institution.

The following stay outside the catalogue unless the scope is deliberately widened again:

- national cyber statutes and national strategies;
- vendor guidance, incident reports, threat-intelligence feeds and private contracts;
- general data-protection law without a cybersecurity-specific obligation;
- news reports about cyber incidents, which belong to the event layer only when they explain an instrument or its absence.

Regional law is included as **regional law**, not as international law. The EU AI Act is already recorded on that basis; NIS2 and the CRA would follow the same rule. National law remains a stated boundary.

## 3. Domain model

Every record gets a `domains` array:

- `["ai"]` — the existing AI records;
- `["cyber"]` — cyber-only records;
- `["ai", "cyber"]` — instruments that are expressly both, such as the EU AI Act's cybersecurity provisions or a cyber treaty with a documented AI hook.

The existing records default to `["ai"]`. A cyber-only record must not be counted in the AI headline figures, the AI-specific treaty count or the AI binding/non-binding totals. The site should show three totals: AI, cyber, and both.

An optional `cyber` block carries only information the generic fields cannot:

- `ai_hooks` — provisions that expressly reach AI systems or AI supply chains;
- `critical_infrastructure_sectors`;
- `product_scope`;
- `supervisory_authority`;
- `cooperation_mechanism` for treaties that create a network, a 24/7 contact point or a joint investigation channel.

The existing fields remain authoritative for legal form, binding status, entry into force, parties, languages, dates, sources, verification, gaps and provenance. Do not create a second schema.

## 4. Candidate families to verify

This is a research register, not a list of confirmed records. Each candidate needs the same treatment as an AI instrument: official text or official status page, exact dates, act type, count basis and field-level provenance.

| Family | Candidates to check | Expected status | What must be verified |
|---|---|---|---|
| Cybercrime treaties | Council of Europe Budapest Convention (ETS 185); First Additional Protocol (ETS 189); Second Additional Protocol (ETS 224); UN Convention against Cybercrime; African Union Malabo Convention; League of Arab States Convention on Combating Information Technology Offences; SCO cooperation agreement | Binding treaties, with different party sets and entry-into-force conditions | Depositary status, parties, reservations, entry into force, cooperation machinery, any AI provision |
| Critical infrastructure and product security | EU NIS2 Directive (EU) 2022/2555; EU Cyber Resilience Act (EU) 2024/2847; comparable regional frameworks | Regional law | Applicability dates, product and supply-chain scope, relationship to the AI Act, supervisory authorities |
| International security norms | UN GGE reports; UN OEWG consensus reports; Paris Call for Trust and Security in Cyberspace; OSCE confidence-building measures | Non-binding political commitments or agreed norms | Which body adopted what; whether the text is an agreed norm, a chair's summary or a unilateral statement |
| Technical standards | ISO/IEC 27001 and 27002; IEC 62443; ISO/IEC 27400 (IoT security) | Private international standards | Edition, scope, whether adoption is contractual or regulatory, AI-specific guidance |
| AI–cyber overlap | EU AI Act cybersecurity articles; CETS 225 risk-management and security duties; Cyber Resilience Act; NIS2 supply-chain duties | Mixed: regional law, treaty, regional law | Exact provisions, cross-links to existing records, whether a separate record is justified |
| Bilateral and multilateral channels | US–UK, US–EU and like-minded cyber dialogues; mutual legal-assistance and 24/7 network arrangements | Political commitments or cooperation channels | Whether an instrument exists, who signed, what obligation or channel it creates |

Candidate examples are included to structure the search. Their inclusion here is not an assertion that they meet the scope rule or that their reported status is correct.

### Audit of 24 November 2026

Covered and mapped: Budapest (ETS 185), ETS 189, CETS 224, the AU Malabo Convention and the UN Cybercrime Convention. Malabo was the material omission found in this audit: it is in force, has a stable official AU status table, and is now a record and a map.

Covered as internal law, not as international binding instruments: NIS2 (Directive (EU) 2022/2555), the Cyber Resilience Act (Regulation (EU) 2024/2847) and the ECOWAS Cybercrime Directive (C/DIR.1/08/11). All are in the catalogue and timeline without boxes and are not mapped as treaties.

Covered as a non-binding cyber instrument: the Paris Call for Trust and Security in Cyberspace (2018). Its official supporters page publishes a downloadable CSV; the official source repository at commit 916433b stores 81 State files. The record maps 81 States and the European Union as political supporters, with the list dated 24 November 2026.

Not added, with the reason stated rather than silently omitted:

- **League of Arab States Convention on Combating Information Technology Offences (2010).** The [official LAS treaty page](http://www.leagueofarabstates.net/ar/legalnetwork/Pages/agreements_details.aspx?RID=73) (RID 73) links the convention text and a ratification table. That table is an official PDF but is undated as a status instrument: its PDF metadata show creation on 24 January 2018, its latest recorded deposit is 20 February 2017, and it records 22 LAS States, 18 signatures and 11 ratifications, with entry into force on 7 February 2014. No current dated depositary table or later official update was verified, so the record and the map are not asserted; the instrument remains a documented gap.
- **SCO Agreement on Cooperation in the Field of International Information Security (2009) and CIS Agreement on Cooperation in Combating Offences related to Computer Information (2001).** Both are identified as regional instruments. Their current status and party lists were not verified from a stable depositary source, so they remain candidates.
- **EU NIS2, the Cyber Resilience Act and the ECOWAS Cybercrime Directive.** Added as internal-law records (`supranational_law` for the two EU acts, `regional_law` for ECOWAS), not as treaties. They are not mapped and do not receive timeline boxes.
- **UN GGE/OEWG cyber reports.** These are non-binding consensus reports, not texts opened for endorsement. The GGE's official list names 25 appointed experts and the OEWG was open to all UN member States; neither list records supporters or adherents. They are therefore not catalogued or mapped as if they had a supporter list. The Paris Call, which does publish a State-level supporter list, is the non-binding cyber record and map.
- **Technical standards (ISO/IEC 27001/27002, IEC 62443).** Private standards, paywalled; no treaty status and no State party table.

This is a completeness check, not a claim that the list is exhaustive. The Arab, CIS and SCO treaties have now been added as metadata-only records; their current depositary tables remain to be verified before any map can be drawn. General information-security cooperation agreements outside the cybercrime/cybersecurity scope (for example the CIS 2013 and CSTO 2017 agreements) remain outside this cycle.

## 5. Derived views

- **Maps.** Only cyber instruments with a published State-level list become maps. The Budapest Convention, ETS 189 and CETS 224 have maps from their Treaty Office tables; the UN Cybercrime Convention has a map from the stable UNTC depositary table; the AU Malabo Convention has a map from the official AU status list dated 2 February 2026; the Paris Call has a map from its official supporter page and the 81 State files in the official source repository at commit 916433b. NIS2, the Cyber Resilience Act and the EU AI Act are internal EU law and remain catalogue-only; they are not mapped as treaties. Section 02 orders the maps treaty-based AI, treaty-based cyber, non-binding AI, non-binding cyber.
- **Timeline.** Keep one chronology, filterable by domain. Cyber-only records must not inherit AI-specific descriptions. Only records with a State-level map get boxes; records without a map and events are plain rows, and every row labels its legal force.
- **Catalogue.** Add a domain filter and a visible `AI`, `Cyber` or `AI + Cyber` label. The existing legal-force, status and verification filters remain.
- **Off the record.** Cyber incidents and policy events enter only when they explain an instrument, a negotiation or an absence; each needs a source and a date.
- **Index.** The 00 statistics split AI, cyber and joint totals. The current AI totals remain reproducible and must not silently absorb cyber records.

## 6. Validation and migration tests

The existing validation contract extends without a second validator:

1. Add `domains` to the schema as a required array with values from `ai` and `cyber`.
2. Migrate every existing record to `domains: ["ai"]`; verify the migration is byte-for-byte deterministic.
3. Require `legal_nature` for a cyber instrument whose form and force are contested, with rationale and source IDs.
4. Require provenance for status, parties, languages and principal provisions; `metadata_verified` must not imply field-level verification.
5. Keep the semantic rules: a domestic approval is not a deposit; `not_applicable` is not zero; a political signature is not a treaty signature; a cyber-only record is not an AI count.
6. Add negative tests for an unknown domain, a missing count basis, a bad date and a party count that exceeds the itemised entries.
7. Add a regression test that the AI headline figures do not change when a cyber-only record is added.
8. Keep the link audit network-only and out of `make test`.

## 7. Phases

**Phase 0 — scope decision (this document).** Adopt the joint AI-and-cyber scope, the domain rule and the separation of counts. No records yet.

**Phase 1 — schema and migration (complete).** Added `domains` and `relevance.cyber_provisions`; migrated all existing records to `["ai"]`; split the build and site counts; renamed the repository and site for the two domains. No cyber record yet.

**Phase 2 — cybercrime treaty pilot (complete for the Budapest family).** The Budapest Convention has an itemised 84-Party table (48 ratifications and 36 accessions), two signatories, eleven further States with no recorded act recorded separately, 96 reservations and 280 declarations/communications/territorial statements, plus a map. ETS 189 and CETS 224 are separate records with itemised party tables and maps. Their reservation/declaration pages are reproduced too: ETS 189 has 21 reservations, 11 declarations and one communication from 16 States; CETS 224 has one reservation and 21 declarations from four States. The UN Cybercrime Convention is added from the UNTC table: 96 signatories (95 States and the EU), three Parties and not in force; the stable table supports the map. Its declarations panel lists 11 reservation paragraphs and four declaration paragraphs for Azerbaijan, Qatar and Viet Nam, now reproduced. The AU Malabo Convention is added from the official AU status list dated 2 February 2026: 55 member States, 21 signatures, 20 Parties, in force since 8 June 2023; 24 member States have no recorded act. The table is stable and supports a map.

**Phase 3 — the cyber hard-law layer (complete for the treaties located in this cycle).** NIS2, the Cyber Resilience Act and the ECOWAS Cybercrime Directive are added as internal-law records, with no timeline boxes and no maps. The Arab Convention, the CIS 2018 Dushanbe Agreement, the CIS 2001 Minsk Agreement and the SCO 2009 Information Security Agreement are added as metadata-only treaties; their current depositary tables are not stable or public, so they are not mapped. The cyber hard-law layer is now nine treaties plus three internal-law acts. Broader information-security cooperation agreements outside the cybercrime/cybersecurity scope (for example the CIS 2013 and CSTO 2017 agreements) are documented as out of scope rather than silently omitted.

**Phase 4 — norms, standards and channels (partly complete).** Three non-binding cyber records and maps are in: the Paris Call (81 States and the EU, official supporters page and repository), the OECD Digital Security Recommendation (39 adherents, OECD Compendium) and the Pall Mall Code (27 supporting States, GOV.UK). The UN GGE/OEWG reports are not mapped because they publish an expert-group membership or open-ended participation, not a list of supporters. The Counter Ransomware Initiative was checked but not added: its public roster is dated May 2024 and does not give a current consolidated list. The OSCE's 57 participating States are a membership, not a supporter list; the Global Cyber Leadership Initiative is an agency network; the Accra Call has mixed State and non-State endorsers without a single official register. The remaining non-binding norms, the international standards and the bilateral cooperation channels are still to be added, each with its own status and verification level. Do not let a political norm inherit the status of a treaty.

**Phase 5 — derived views (partly complete).** The five cyber treaty maps and the three non-binding cyber maps are in the atlas, and section 02 is grouped by treaty-based AI, treaty-based cyber, non-binding AI and non-binding cyber. The timeline filter, the catalogue domain filter and a separate cyber reading list remain to be built. The naming decision has already been made: the repository is `international-ai-cybersecurity-law-corpus` and the site title is **International AI and Cybersecurity Law**, with **Atlas** as its subtitle.

## 8. Open questions

1. ~~Does “all international cybersecurity law” include regional law such as NIS2 and the CRA?~~ Resolved by the maintainer on 24 November 2026: internal law is included as `supranational_law` (EU) or `regional_law` (ECOWAS), but it is not treated as international binding law. It is catalogued and shown in the timeline without a box and is not mapped as a treaty.
2. Do technical standards belong in the same catalogue as treaties? The AI corpus already includes ISO/IEC standards, so consistency favours inclusion, but the cyber standards set is larger and will need a selection rule.
3. Should the UN Cybercrime Convention be mapped before its party table is stable? The UNTC table is stable and distinguishes signatures from deposits, so it is mapped. A treaty map requires a depositary act, not a signature list inferred from a press release.
4. How should the site present joint AI–cyber instruments? Use `domains: ["ai", "cyber"]` and show them in both filtered views, but count them once in the joint total.
5. ~~Does the title change?~~ Resolved by the maintainer on 24 November 2026: the repository is now `international-ai-cybersecurity-law-corpus` and the site title is **International AI and Cybersecurity Law**, with **Atlas** as its subtitle. The AI counts remain visible and separate from the cyber counts.

## 9. What this plan does not do

It does not add the timeline/catalogue domain filters or the remaining norms and standards. The catalogue now contains 48 AI-layer records plus 15 cybersecurity-only records (nine treaties, three internal-law acts and three non-binding instruments): 63 in total, 22 with binding form (18 international — 13 in force and five not confirmed — and four internal law) and 41 non-binding, with seventeen maps. The mapped cyber treaties have itemised party tables; the Arab, CIS and SCO treaties are metadata-only because their depositary tables are unavailable or unstable. None asserts an AI provision. The next implementation step is Phase 4: non-binding norms, cyber standards and cooperation channels, each with its own status and verification level.
