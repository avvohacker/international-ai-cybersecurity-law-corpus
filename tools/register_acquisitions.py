#!/usr/bin/env python3
"""Build catalog/acquisitions.json from a URL map and the stored originals."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
OUT = ROOT / "catalog" / "acquisitions.json"

ACCESSED = "2026-11-23"

# (instrument_id, dest, url, media_type, note)
SOURCES = [
    (
        "un-ga-res-78-265",
        "source/A_RES_78_265-en.pdf",
        "https://documents.un.org/api/symbol/access?l=en&s=A%2FRES%2F78%2F265&t=pdf",
        "application/pdf",
        "Official UN document A/RES/78/265 (English).",
    ),
    (
        "un-ga-res-78-311",
        "source/A_RES_78_311-en.pdf",
        "https://documents.un.org/api/symbol/access?l=en&s=A%2FRES%2F78%2F311&t=pdf",
        "application/pdf",
        "Official UN document A/RES/78/311 (English).",
    ),
    (
        "un-ga-res-78-241",
        "source/A_RES_78_241-en.pdf",
        "https://documents.un.org/api/symbol/access?l=en&s=A%2FRES%2F78%2F241&t=pdf",
        "application/pdf",
        "Official UN document A/RES/78/241 (English).",
    ),
    (
        "un-ga-res-79-62",
        "source/A_RES_79_62-en.pdf",
        "https://digitallibrary.un.org/record/4071100/files/A_RES_79_62-EN.pdf",
        "application/pdf",
        "Official UN document A/RES/79/62 (English).",
    ),
    (
        "un-ga-res-79-239",
        "source/A_RES_79_239-en.pdf",
        "https://documents.un.org/api/symbol/access?l=en&s=A%2FRES%2F79%2F239&t=pdf",
        "application/pdf",
        "Official UN document A/RES/79/239 (English).",
    ),
    (
        "un-ga-res-79-325",
        "source/A_RES_79_325-en.pdf",
        "https://digitallibrary.un.org/nanna/record/4087699/files/A_RES_79_325-EN.pdf?withWatermark=0&withMetadata=0&registerDownload=1&version=1",
        "application/pdf",
        "Official UN document A/RES/79/325 (English).",
    ),
    (
        "un-ga-res-79-1",
        "source/A_RES_79_1-en.pdf",
        "https://documents.un.org/api/symbol/access?l=en&s=A%2FRES%2F79%2F1&t=pdf",
        "application/pdf",
        "Official UN document A/RES/79/1 (English), including the Global Digital Compact annex.",
    ),
    (
        "un-ga-res-80-57",
        "source/A_RES_80_57-en.pdf",
        "https://documents.un.org/api/symbol/access?l=en&s=A%2FRES%2F80%2F57&t=pdf",
        "application/pdf",
        "Official UN document A/RES/80/57 (English).",
    ),
    (
        "un-ga-res-80-58",
        "source/A_RES_80_58-en.pdf",
        "https://documents.un.org/api/symbol/access?l=en&s=A%2FRES%2F80%2F58&t=pdf",
        "application/pdf",
        "Official UN document A/RES/80/58 (English).",
    ),
    (
        "depa-2020",
        "source/DEPA-signing-text-2020-06-11-en.pdf",
        "https://fta.motir.go.kr/webmodule/_PSD_FTA/support/DEPA/depa_all_eng.pdf",
        "application/pdf",
        "Signing text of the Digital Economy Partnership Agreement, reproduced by the Republic of Korea Ministry of Trade, Industry and Energy; depositary is New Zealand.",
    ),
    (
        "sadea-2020",
        "source/SADEA-2020-08-06-en.pdf",
        "https://isomer-user-content.by.gov.sg/1004/769c26eb-17cf-4e2d-962b-1277a22df9db/australia-singapore-digital-economy-agreement%20-%20Jun%2023.pdf",
        "application/pdf",
        "Australia-Singapore Digital Economy Agreement, text reproduced on the Singapore Government Isomer platform.",
    ),
    (
        "paris-ai-action-summit-statement-2025",
        "source/statement-2025-02-11-en.pdf",
        "https://www.elysee.fr/admin/upload/default/0001/17/0efc53b2025d5bc1f0fc68556c41370cee166e7f.pdf",
        "application/pdf",
        "Official Élysée PDF of the Paris AI Action Summit statement, published 19 February 2025.",
    ),
    (
        "china-global-ai-governance-initiative-2023",
        "source/global-ai-governance-initiative-en.html",
        "https://www.mfa.gov.cn/mfa_eng/zy/gb/202405/t20240531_11367503.html",
        "text/html; charset=utf-8",
        "Official English text of China's Global AI Governance Initiative, Ministry of Foreign Affairs.",
    ),
    (
        "g7-hiroshima-code-2023",
        "source/HAIP-Code-of-Conduct-2023-10-30-en.pdf",
        "https://www.soumu.go.jp/hiroshimaaiprocess/pdf/document05_en.pdf",
        "application/pdf",
        "Hiroshima Process International Code of Conduct, official Japanese MIC publication.",
    ),
    (
        "oecd-ai-recommendation-2019",
        "source/OECD-LEGAL-0449-en.pdf",
        "https://legalinstruments.oecd.org/public/doc/648/648.en.pdf",
        "application/pdf",
        "OECD/LEGAL/0449, official OECD Legal Instruments booklet (2024 revision).",
    ),
    (
        "coe-cets-225",
        "source/cets-225-en-ohchr-2026-11-25.pdf",
        "https://www.ohchr.org/sites/default/files/documents/cfi-subm/244-artificial-intelligence/subm-artificial-intelligence-igo-13-council-europe-publications-annex-2.pdf",
        "application/pdf",
        "12-page Council of Europe Treaty Series PDF of CETS 225, reproduced in an OHCHR submission annex. Official reproduction, not the certified corrected copy adopted on 30 April 2025.",
        "2026-11-25",
    ),
    (
        "coe-cets-225",
        "source/cets-225-fr-en-certified-2025-05-20.pdf",
        "https://rm.coe.int/1680b680bc",
        "application/pdf",
        "Certified bilingual copy of CETS 225 in its corrected French version, adopted under the Committee of Ministers decision of 30 April 2025 and dated Strasbourg, 20 May 2025. Includes the authentic French text; 27 PDF pages, two columns.",
        "2026-11-25",
    ),
    (
        "brics-ai-statement-2025",
        "source/brics-ggai-declaration-2025-07-06-en.pdf",
        "https://web.archive.org/web/20260418114944/https://brics.br/en/documents/presidency-documents/250706_brics_ggai_declarationfinal.pdf/@@download/file",
        "application/pdf",
        "Archived copy (Internet Archive, snapshot 18 April 2026) of the official BRICS 2025 Presidency PDF of the Leaders' Statement on the Global Governance of Artificial Intelligence, adopted in Rio de Janeiro on 6 July 2025. The live brics.br host did not resolve by DNS from this environment.",
        "2026-11-25",
    ),
    (
        "cis-minsk-agreement-2001",
        "source/cis-minsk-agreement-2001-en-translation.pdf",
        "https://web.archive.org/web/20220320005205/https://copat.gov.az/docs/Qanunvericilik/Agreement%20on%20Cooperation%20in%20Combating%20Offences%20related%20to%20Computer%20Information%20-%20Commonwealth%20of%20Independent%20States.pdf",
        "application/pdf",
        "Archived copy (Internet Archive, snapshot 20 March 2022) of the English translation of the 2001 CIS Minsk Agreement reproduced by the Prosecutor General's Office of Azerbaijan. The live host fails TLS certificate verification from this environment.",
        "2026-11-25",
    ),
    (
        "paris-call-cyberspace-2018",
        "source/paris-call-2018-11-12-en.pdf",
        "https://web.archive.org/web/20240927054607/https://pariscall.international/assets/files/paris-call.pdf",
        "application/pdf",
        "Archived copy (Internet Archive, snapshot 27 September 2024) of the official four-page English PDF of the Paris Call for Trust and Security in Cyberspace, dated 12 November 2018. The live pariscall.international host no longer resolves from this environment.",
        "2026-11-25",
    ),
    (
        "unesco-ethics-ai-2021",
        "source/unesco-ai-ethics-recommendation-2022-en.pdf",
        "https://web.archive.org/web/20261029235825/https://unesdoc.unesco.org/in/rest/annotationSVC/DownloadWatermarkedAttachment/attach_import_75c9fb6b-92a6-4982-b772-79f540c9fc39?_=381137eng.pdf",
        "application/pdf",
        "Archived copy (Internet Archive, snapshot 29 October 2026) of the English PDF of the UNESCO Recommendation on the Ethics of Artificial Intelligence, adopted on 23 November 2021 (SHS/BIO/PI/2021/1, 43 pages). The live UNESDOC PDF endpoint returned HTTP 403 to automated clients.",
        "2026-11-25",
    ),
    (
        "coe-cets-225-explanatory-report",
        "source/cets-225-explanatory-report-2024-09-05-en.pdf",
        "https://web.archive.org/web/20261117082757/https://rm.coe.int/1680afae67",
        "application/pdf",
        "Archived copy (Internet Archive, snapshot 17 November 2026) of the official English Explanatory Report to CETS 225, dated Vilnius, 5 September 2024. The live rm.coe.int endpoint returned HTTP 403 to automated clients.",
        "2026-11-25",
    ),
    (
        "afcfta-digital-trade-protocol-2024",
        "source/afcfta-digital-trade-protocol-2025-en.pdf",
        "https://au.int/sites/default/files/treaties/44963-treaty-EN_-_Protocol_to_AfCFTA_Agreement_on_Digital_Trade.pdf",
        "application/pdf",
        "Official English text of the Protocol to the AfCFTA Agreement on Digital Trade, 24 pages. Main Protocol only; the separately adopted annexes are stored as a compiled PDF.",
        "2026-11-25",
    ),
    (
        "afcfta-digital-trade-protocol-2024",
        "source/afcfta-digital-trade-annexes-2025-en.pdf",
        "https://au.int/sites/default/files/treaties/44963-ax-ENG_Circulation_Digital_Trade_Compiled_Certified_Legal_Instruments_38thAssembly_Feb_2025_27_May2025.pdf",
        "application/pdf",
        "Official compiled annexes to the AfCFTA Digital Trade Protocol, adopted by the 38th Ordinary Session of the Assembly in February 2025, 52 pages. Includes the Annex on Emerging and Advanced Technologies.",
        "2026-11-25",
    ),
    (
        "afcfta-digital-trade-protocol-2024",
        "source/afcfta-emerging-tech-annex-2025-en.pdf",
        "https://au.int/sites/default/files/treaties/44963-ax-ENG_Circulation_Digital_Trade_Compiled_Certified_Legal_Instruments_38thAssembly_Feb_2025_27_May2025.pdf",
        "application/pdf",
        "Pages 25-30 of the official compiled annexes: Annex on Emerging and Advanced Technologies. Extracted as a separate PDF for text and unit anchors; the complete compiled annexes are stored separately.",
        "2026-11-25",
    ),
    (
        "arab-convention-it-offences-2010",
        "source/arab-convention-2010-ar-archive.pdf",
        "https://web.archive.org/web/20240423123401/https://www.leagueofarabstates.net/ar/legalnetwork/Documents/%D8%A7%D9%84%D8%A7%D8%AA%D9%81%D8%A7%D9%82%D9%8A%D8%A9%20%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9%20%D9%84%D9%85%D9%83%D8%A7%D9%81%D8%AD%D8%A9%20%D8%AC%D8%B1%D8%A7%D8%A6%D9%85%20%D8%AA%D9%82%D9%86%D9%8A%D8%A9%20%D8%A7%D9%84%D9%85%D8%B9%D9%84%D9%88%D9%85%D8%A7%D8%AA.pdf",
        "application/pdf",
        "Archived official Arabic text of the Arab Convention on Combating Information Technology Offences, from the League of Arab States legal network (Internet Archive snapshot 23 April 2024).",
        "2026-11-25",
    ),
    (
        "arab-convention-it-offences-2010",
        "source/arab-convention-2010-en-reproduction.pdf",
        "https://www.asianlaws.org/gcld/cyberlawdb/GCC/Arab%20Convention%20on%20Combating%20Information%20Technology%20Offences.pdf",
        "application/pdf",
        "English reproduction of the Arab Convention published by AsianLaws. It is a working translation/reproduction, not an official League of Arab States English text; the official Arabic PDF is stored alongside it.",
        "2026-11-25",
    ),
    (
        "au-malabo-convention-2014",
        "source/au-malabo-convention-2014-en-scanned.pdf",
        "https://au.int/sites/default/files/treaties/29560-treaty-0048_-_african_union_convention_on_cyber_security_and_personal_data_protection_e.pdf",
        "application/pdf",
        "Official English PDF of the African Union Convention on Cyber Security and Personal Data Protection. The PDF is image-only (no text layer); the scanned official copy is authoritative.",
        "2026-11-25",
    ),
    (
        "au-malabo-convention-2014",
        "source/au-malabo-convention-2014-en-senlii-transcription.pdf",
        "https://senlii.org/en/akn/aa-au/act/convention/2014/cyber-security-and-personal-data-protection/eng@2014-06-27/source.pdf",
        "application/pdf",
        "English transcription of the Malabo Convention from the AfricanLII network (SenLII), generated 11 June 2026. Used for the searchable text because the official PDF has no text layer; it is a legal-database transcription, not an official translation.",
        "2026-11-25",
    ),
    (
        "budapest-convention-2001",
        "source/budapest-convention-2001-en.pdf",
        "https://rm.coe.int/1680081561",
        "application/pdf",
        "Official Council of Europe English text of the Budapest Convention (ETS 185), 22 pages.",
        "2026-11-25",
    ),
    (
        "cis-it-crimes-agreement-2018",
        "source/cis-2018-agreement-ru.html",
        "https://eccis.org/document/5864",
        "text/html; charset=utf-8",
        "Official Russian text of the 2018 CIS Agreement on cooperation in combating information-technology crimes, from the CIS Executive Committee. The English translation on the same page is machine-generated and paywalled, so it is not used.",
        "2026-11-25",
    ),
    (
        "coe-cets-224",
        "source/cets-224-en-2022.pdf",
        "https://web.archive.org/web/20220516075219/https://rm.coe.int/1680a49dab",
        "application/pdf",
        "Archived official Council of Europe English PDF of the Second Additional Protocol to the Budapest Convention (CETS 224), 21 pages. The live rm.coe.int URL returned HTTP 403 to automated clients on 25 November 2026.",
        "2026-11-25",
    ),
    (
        "coe-ets-189",
        "source/ets-189-en-2003.pdf",
        "https://web.archive.org/web/2024/https://rm.coe.int/168008160f",
        "application/pdf",
        "Archived official Council of Europe English PDF of the Additional Protocol to the Budapest Convention on racist and xenophobic acts (ETS 189), 6 pages. The live rm.coe.int URL returned HTTP 403 to automated clients on 25 November 2026.",
        "2026-11-25",
    ),
    (
        "ecowas-cybercrime-directive-2011",
        "source/ecowas-cybercrime-directive-2011-en.pdf",
        "https://www.ecowas.int/wp-content/uploads/2025/05/SIGNED-Cyber-Crime.pdf",
        "application/pdf",
        "Official signed English PDF of ECOWAS Directive C/DIR.1/08/11 on Fighting Cyber Crime. The PDF is image-only; the searchable text is OCR produced from this official scan.",
        "2026-11-25",
    ),
    (
        "iccpr-1966",
        "source/iccpr-1966-en.pdf",
        "https://www.ohchr.org/sites/default/files/ccpr.pdf",
        "application/pdf",
        "Official OHCHR English PDF of the International Covenant on Civil and Political Rights, 26 pages.",
        "2026-11-25",
    ),
    (
        "ksdpa-2022",
        "source/ksdpa-2022-en.pdf",
        "https://fta.motir.go.kr/webmodule/_PSD_FTA/ksdpa/1/KSDPA_eng.pdf",
        "application/pdf",
        "English text of the Korea-Singapore Digital Partnership Agreement, reproduced by the Republic of Korea Ministry of Trade, Industry and Energy.",
        "2026-11-25",
    ),
    (
        "sco-information-security-agreement-2009",
        "source/sco-2009-en.pdf",
        "https://eng.sectsco.org/files/207508/207508",
        "application/pdf",
        "Official English PDF of the 2009 SCO Agreement on Cooperation in Ensuring International Information Security, 13 pages.",
        "2026-11-25",
    ),
    (
        "uksdea-2022",
        "source/uksdea-2022-en.pdf",
        "https://assets.publishing.service.gov.uk/media/64c14f401e10bf000e17cfa9/TS_22.2023_UK_Singapore_Digital_Economy_Agreement.pdf",
        "application/pdf",
        "Official UK Treaty Series No. 22 (2023) English text of the UK-Singapore Digital Economy Agreement, 49 pages.",
        "2026-11-25",
    ),
    (
        "un-cybercrime-convention-2024",
        "source/un-cybercrime-convention-2024-en-certified.pdf",
        "https://treaties.un.org/doc/Treaties/2024/12/20241224%2001-27%20PM/Ch_XVIII_16.pdf",
        "application/pdf",
        "Certified true copy of the United Nations Convention against Cybercrime (XVIII-16), 388 pages, containing the six authentic language versions.",
        "2026-11-25",
    ),
    (
        "un-cybercrime-convention-2024",
        "source/un-cybercrime-convention-2024-en-extract.pdf",
        "https://treaties.un.org/doc/Treaties/2024/12/20241224%2001-27%20PM/Ch_XVIII_16.pdf",
        "application/pdf",
        "English extract of the certified copy: pages 59-118 of the 388-page multilingual PDF, containing the complete English text (Articles 1-68). Extracted as a separate PDF for text and page anchors.",
        "2026-11-25",
    ),
    (
        "vclt-1969",
        "source/vclt-1969-en.pdf",
        "https://legal.un.org/ilc/texts/instruments/english/conventions/1_1_1969.pdf",
        "application/pdf",
        "Official United Nations English PDF of the Vienna Convention on the Law of Treaties, 1969, 31 pages.",
        "2026-11-25",
    ),
    (
        "waico-establishment-agreement-2026",
        "source/waico-agreement-2026-zh.html",
        "http://www.npc.gov.cn/npc/c2/c30834/202611/t20261118_458879.html",
        "text/html; charset=utf-8",
        "Official Chinese text of the Agreement on the Establishment of the World Artificial Intelligence Cooperation Organization, published by the National People's Congress on 18 November 2026. The page is served over HTTP; HTTPS did not complete a TLS handshake from this environment.",
        "2026-11-25",
    ),
    (
        "bletchley-declaration-2023",
        "source/bletchley-declaration-2023-en.html",
        "https://www.gov.uk/government/publications/ai-safety-summit-2023-the-bletchley-declaration/the-bletchley-declaration-by-countries-attending-the-ai-safety-summit-1-2-november-2023",
        "text/html; charset=utf-8",
        "Official GOV.UK HTML publication of the Bletchley Declaration, including the list of participating countries and the note recording New Zealand's accession on 23 October 2024.",
        "2026-11-26",
    ),
    (
        "seoul-declaration-2024",
        "source/seoul-declaration-2024-en.html",
        "https://www.gov.uk/government/publications/seoul-declaration-for-safe-innovative-and-inclusive-ai-ai-seoul-summit-2024/seoul-declaration-for-safe-innovative-and-inclusive-ai-by-participants-attending-the-leaders-session-ai-seoul-summit-21-may-2024",
        "text/html; charset=utf-8",
        "Official GOV.UK HTML publication of the Seoul Declaration adopted at the Leaders' Session of the AI Seoul Summit on 21 May 2024.",
        "2026-11-26",
    ),
    (
        "frontier-ai-safety-commitments-2024",
        "source/frontier-ai-safety-commitments-2024-en.html",
        "https://www.gov.uk/government/publications/frontier-ai-safety-commitments-ai-seoul-summit-2024/frontier-ai-safety-commitments-ai-seoul-summit-2024",
        "text/html; charset=utf-8",
        "Official GOV.UK HTML publication of the Frontier AI Safety Commitments, including the initial and later endorsing organisations and the footnotes.",
        "2026-11-26",
    ),
    (
        "g7-digital-technology-ministerial-declaration-2026",
        "source/g7-digital-technology-ministerial-declaration-2026-en.html",
        "https://www.gov.uk/government/publications/g7-digital-and-technology-ministerial-declaration-29-may-2026/g7-digital-and-technology-ministerial-declaration-29-may-2026",
        "text/html; charset=utf-8",
        "Official English text of the G7 Digital and Technology Ministerial Declaration, published by the UK Department for Science, Innovation and Technology on 1 June 2026.",
        "2026-11-26",
    ),
    (
        "reaim-call-to-action-2023",
        "source/reaim-2023-call-to-action-en.pdf",
        "https://www.government.nl/site/binaries/site-content/collections/documents/2023/02/16/reaim-2023-call-to-action/REAIM+2023+Call+to+Action.pdf",
        "application/pdf",
        "Official four-page English PDF of the REAIM 2023 Call to Action, published by the Government of the Netherlands.",
        "2026-11-26",
    ),
    (
        "reaim-pathways-to-action-2026",
        "source/reaim-2026-pathways-to-action-en.pdf",
        "https://exteriores.gob.es/en/REAIM2026/Documents/REAIM%202026%20Pathways%20to%20Action.pdf",
        "application/pdf",
        "Official eight-page English PDF of the REAIM 2026 Pathways to Action, published by the Spanish Ministry of Foreign Affairs, European Union and Cooperation.",
        "2026-11-26",
    ),
    (
        "asean-ai-guide-2024",
        "source/asean-ai-guide-2024-en.pdf",
        "https://asean.org/wp-content/uploads/2024/02/ASEAN-Guide-on-AI-Governance-and-Ethics_beautified_201223_v2.pdf",
        "application/pdf",
        "Official 87-page English PDF of the ASEAN Guide on AI Governance and Ethics, published by the ASEAN Secretariat.",
        "2026-11-26",
    ),
    (
        "au-continental-ai-strategy-2024",
        "source/au-continental-ai-strategy-2024-en.pdf",
        "https://au.int/sites/default/files/documents/44004-doc-EN-_Continental_AI_Strategy_July_2024.pdf",
        "application/pdf",
        "Official 66-page English PDF of the African Union Continental Artificial Intelligence Strategy, published by the African Union Commission.",
        "2026-11-26",
    ),
    (
        "un-hrc-res-63-15",
        "source/A_HRC_RES_63_15-en.pdf",
        "https://digitallibrary.un.org/record/4130748/files/A_HRC_RES_63_15-EN.pdf",
        "application/pdf",
        "Official six-page English PDF of Human Rights Council resolution 63/15, A/HRC/RES/63/15, adopted on 6 October 2026.",
        "2026-11-26",
    ),
]


def main() -> int:
    records = []
    for source in SOURCES:
        iid, dest, url, media, note = source[:5]
        accessed = source[5] if len(source) > 5 else ACCESSED
        path = CORPUS / iid / dest
        if not path.exists():
            raise SystemExit(f"missing stored file: {path}")
        records.append(
            {
                "instrument_id": iid,
                "dest": dest,
                "url": url,
                "sha256": __import__("hashlib").sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
                "accessed": accessed,
                "media_type": media,
                "note": note,
            }
        )
    records.sort(key=lambda r: (r["instrument_id"], r["dest"]))
    OUT.write_text(
        json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(records)} acquisition record(s) to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
