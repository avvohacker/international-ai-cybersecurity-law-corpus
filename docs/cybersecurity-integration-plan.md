# Cybersecurity integration plan

**Status:** proposal only. Nothing in this plan has been implemented, and no cybersecurity record has been added to the catalogue. This note describes how the existing corpus architecture could absorb cybersecurity instruments without turning the atlas into a general international-law database.

## 1. Why a separate plan

The corpus is currently an AI-law corpus. Cybersecurity is a neighbouring field with its own treaties, regional law, technical standards and political commitments. Some instruments overlap directly with AI (the EU AI Act's cybersecurity requirements, the Cyber Resilience Act, CETS 225's risk-management duties, NIS2 supply-chain duties); many do not. Adding cybersecurity therefore needs a scope rule, not a bulk import.

The purpose of the integration is to answer a narrow question: **which cybersecurity instruments impose, or fail to impose, obligations that reach AI systems, AI supply chains or AI-enabled critical infrastructure?** A second, descriptive layer may cover the general cybersecurity law that AI operators actually face, but it must be marked as context rather than as AI-specific law.

## 2. Scope rule

A cybersecurity record enters the catalogue only if at least one of the following holds:

1. it contains an express AI, automated-decision or AI-supply-chain provision;
2. it governs the security of critical infrastructure or digital products in a way that directly applies to AI systems or their providers;
3. it is a treaty or framework that the AI instruments expressly rely on, incorporate or implement.

General cybersecurity law that meets none of these tests stays outside the catalogue, even if it is important. A separate `context` collection can be added later without changing the AI-law counts. This preserves the meaning of the existing headline number.

## 3. Candidate families (to verify, not assumed)

The first cycle should check these families against official sources:

| Family | Candidate examples | Expected relevance | Verification needed |
|---|---|---|---|
| Cybercrime treaties | Council of Europe Budapest Convention (ETS 185) and its protocols; UN Convention against Cybercrime | Criminal-procedure and cooperation background; not AI-specific | Status, parties, entry into force, whether any AI provision exists |
| Critical-infrastructure and product law | EU NIS2 Directive (EU) 2022/2555; EU Cyber Resilience Act (EU) 2024/2847 | Supply-chain and product-security duties that reach AI providers in the EU | Applicability dates, AI-specific recitals or annexes, relationship to the AI Act |
| International security norms | UN GGE/OEWG norms; bilateral cyber dialogues; Paris Call for Trust and Security in Cyberspace | Political commitments, not treaties; useful for the “off the record” layer | Which body adopted what, and whether the text is an agreed norm or a chair's summary |
| Technical standards | ISO/IEC 27001 and 27002; IEC 62443; NIST CSF | Private standards, binding only through contract, procurement or regulation | Version, scope, whether AI-specific guidance exists |
| AI-security guidance | NIST AI RMF and its generative-AI profile; UK/EU AI-security guidance | Soft law and technical guidance; may already be candidates in the AI corpus | Whether they belong to the AI corpus or to the cyber context layer |
| Regional and national law | EU AI Act cybersecurity articles; national cyber statutes | Regional law is already represented by the EU AI Act; national law is outside the current scope | Keep out unless the scope rule changes |

This table is a research agenda, not a list of confirmed records. Each candidate needs the same treatment as an AI instrument: official text or official status page, exact dates, act type, count basis and field-level provenance.

## 4. Data model

Reuse the existing record structure. Do not create a second schema unless a field cannot be expressed.

- Add a top-level `domains` array (`["ai"]`, `["cyber"]`, `["ai","cyber"]`) with a default of `["ai"]` for existing records. This is the only new structural field needed for filtering and for keeping the headline AI count stable.
- Add an optional `cyber` block only where it carries information the generic fields cannot: `ai_hooks` (array of provisions that reach AI), `critical_infrastructure_sectors`, `product_scope`, `supervisory_authority`.
- Reuse `instrument_type`, `binding_status`, `legal_nature`, `status`, `parties`, `languages`, `dates`, `sources`, `verification`, `gaps` and `provenance` unchanged.
- Reuse `parties.act` for treaty signature, accession, ratification and political signature. A cyber treaty's parties are not `signatories_total`.
- Keep `counts` bases (`verified_total`, `declared_total`, `zero_verified`, `unknown`, `not_applicable`). A cyber instrument with no depositary table gets `unknown`, not zero.

If a future record needs a genuinely new act type, extend the schema enum with a documented definition and a negative test; do not overload `signatures`.

## 5. Derived representations

- **Maps.** Only instruments with a published State-level list become maps. Do not invent a “cyber map” from membership in an organisation. A Budapest Convention map is possible if the Treaty Office chart is stored; a NIS2 map is not, because it is EU law, not a treaty.
- **Timeline.** Cyber records use the same two-column timeline and the same text slot: why the instrument exists, what it changed, what it left out. Keep AI and cyber records in one chronology if the page remains an AI atlas; use the `domains` field for filtering rather than for a second timeline.
- **Off the record.** Add cyber-specific unseen events only when they explain the absence of an instrument: a summit that ended without a text, a hotline or bilateral channel, a market incident that changed the agenda. Each needs a source and a date, as with the current eight events.
- **Catalogue.** Add a domain filter and a visible label. A cyber-only record must not be counted in “AI-specific treaties” or in the AI binding/non-binding totals.

## 6. Validation and tests

The existing validation contract extends without a second validator:

1. Apply the same JSON Schema, with `domains` and the optional `cyber` block.
2. Require `legal_nature` for any cyber instrument whose form and force are contested, with rationale and source IDs.
3. Require `provenance.assertions` for status, parties, languages and principal provisions; a `metadata_verified` level must not imply field-level verification.
4. Keep semantic checks separate: a domestic approval is not a deposit; `not_applicable` is not zero; a political signature is not a treaty signature.
5. Add negative tests for a cyber record with a missing count basis, a bad date, an unknown `domains` value and a party count that exceeds the itemised entries.
6. Add a regression test that the AI headline counts do not change when a cyber-only record is added.
7. Keep the link audit network-only and out of `make test`.

## 7. Phases

**Phase 0 — scope and inventory (no records).** Confirm the scope rule with the maintainer; list candidate families and their official registers; decide whether a separate `context` collection is wanted. Output: this plan, updated with decisions.

**Phase 1 — one treaty pilot.** Choose one cyber treaty with a public depositary chart (Budapest Convention is the obvious candidate) and build a full record: official text, status snapshot, parties, counts, provenance, gaps. Do not map it until the data are complete. Output: one record, one validation run, no site change beyond a hidden or clearly labelled entry.

**Phase 2 — AI-cyber overlap.** Add the instruments that directly reach AI: the EU AI Act's cybersecurity provisions (already in the corpus, so add `domains` and `cyber.ai_hooks` rather than a duplicate), the Cyber Resilience Act, NIS2 where the AI supply-chain link is documented. Output: cross-links from existing AI records, not duplicate records.

**Phase 3 — derived views.** Add the domain filter, a cyber timeline slot and, if the data support it, one map. Add “off the record” cyber events only with sources. Output: site changes gated on the same tests as the AI atlas.

**Phase 4 — review.** Re-run the source-family checklist, the link audit and the coverage matrix; decide whether the atlas is still “international AI law” or has become a two-domain corpus. That naming decision belongs to the maintainer, not to the data migration.

## 8. Open questions

1. Is the goal an AI-law corpus with cyber context, or a joint AI-and-cyber corpus? The answer changes the title, the counts and the navigation.
2. Should EU regulations other than the AI Act be admitted? The current rule admits only the AI Act as supranational law; NIS2 and the CRA would break that rule unless the scope is widened deliberately.
3. Should national cyber statutes be admitted? The current corpus excludes national legislation; admitting them would create an open-ended collection with no stable boundary.
4. Which body's status page is authoritative for the UN cybercrime convention, and is a public party table available? If not, the count must be `unknown`, as with WAICO.
5. Do technical standards belong in the same catalogue as treaties? The AI corpus already includes ISO/IEC standards as metadata-only records, so consistency favours inclusion, but the cyber standards set is much larger.

## 9. What this plan does not do

It does not add records, schema fields, maps, tests or site sections. It does not assert that any candidate instrument contains an AI provision. It does not change the current counts: 46 records, 10 binding, 36 non-binding. Implementation starts only after the scope question in §8.1 is answered.
