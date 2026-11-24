# Cybersecurity integration plan

**Status:** Phase 2 started. The corpus is a joint **AI and international cybersecurity law** corpus in structure and has its first cybersecurity-only record, the Budapest Convention (ETS 185), metadata-verified with a declared 84-Party count. The party-level list, the protocols and a map remain pending. The AI layer remains 46 records; the total is now 47.

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

## 5. Derived views

- **Maps.** Only cyber instruments with a published State-level list become maps. The Budapest Convention and the UN Cybercrime Convention are candidates if a depositary table is stored; NIS2 is not a treaty and should not be mapped as one.
- **Timeline.** Keep one chronology, filterable by domain. Cyber-only records must not inherit AI-specific descriptions. The same rule applies as in section 03: only route-changing texts get boxes, the rest are compact records.
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

**Phase 2 — cybercrime treaty pilot (started).** The Budapest Convention is catalogued as a metadata-only record: official title, opening and entry-into-force dates, 84 declared Parties and the cyber provisions it governs. The next pass must itemise the party list, record reservations and declarations, and decide whether to add the two protocols. The UN Cybercrime Convention is the second candidate once its depositary picture is clear. No map until the party data are complete.

**Phase 3 — the cyber hard-law layer.** Add the remaining cybercrime treaties and the regional product/critical-infrastructure law. Record the EU AI Act's cybersecurity provisions as cross-links on the existing AI record rather than as a duplicate. Output: the cyber catalogue, still separate from AI counts.

**Phase 4 — norms, standards and channels.** Add the non-binding UN norms, the international standards and the bilateral cooperation channels, each with its own status and verification level. Do not let a political norm inherit the status of a treaty.

**Phase 5 — derived views.** Add the cyber maps, the timeline filter and the cyber reading list. The naming decision has already been made: the repository is `international-ai-cybersecurity-law-corpus` and the site title is **International AI and Cybersecurity Law**, with **Atlas** as its subtitle. The views still have to catch up with the name.

## 8. Open questions

1. Does “all international cybersecurity law” include regional law such as NIS2 and the CRA? This plan says yes, marked as regional law, because the AI corpus already admits the EU AI Act on that basis.
2. Do technical standards belong in the same catalogue as treaties? The AI corpus already includes ISO/IEC standards, so consistency favours inclusion, but the cyber standards set is larger and will need a selection rule.
3. Should the UN Cybercrime Convention be mapped before its party table is stable? No. A treaty map requires a deposited act, not a signature list inferred from a press release.
4. How should the site present joint AI–cyber instruments? Use `domains: ["ai", "cyber"]` and show them in both filtered views, but count them once in the joint total.
5. ~~Does the title change?~~ Resolved by the maintainer on 24 November 2026: the repository is now `international-ai-cybersecurity-law-corpus` and the site title is **International AI and Cybersecurity Law**, with **Atlas** as its subtitle. The AI counts remain visible and separate from the cyber counts.

## 9. What this plan does not do

It does not add the remaining cybersecurity records, maps or site sections. The catalogue now contains 46 AI-layer records plus the Budapest Convention as one cybersecurity-only record: 47 in total, 11 binding and 36 non-binding. The Budapest record is metadata-level and does not assert an AI provision. The next implementation step is Phase 2 completion: itemise the Budapest party list and add the protocols or the UN Cybercrime Convention.
