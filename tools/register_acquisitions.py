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
