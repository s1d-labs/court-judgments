"""Pure parsers for AWS Open Data court metadata (indian-high-court-judgments / -supreme-court-judgments). Testable offline."""
import re
VS = re.compile(r'\s+(?:vs?\.?|v/s|versus)\s+', re.I)

def parties(title):
    """(petitioner, respondent) from a cause title like 'CR. MISC./68032/2022 of X Vs Y' or 'X Vs Y'."""
    if not title: return None, None
    t = title.strip()
    m = re.search(r'\bof\s+(.+)$', t)       # drop the leading case-number descriptor
    core = m.group(1) if m else t
    parts = VS.split(core, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(" .,")[:300], parts[1].strip(" .,")[:300]
    return core.strip(" .,")[:300], None

def row_meta(r):
    """One metadata/parquet row -> (cnr, data). HC + SC share these fields."""
    cnr = r.get("cnr") or r.get("diary_number") or r.get("title")
    if not cnr: return None
    pet, resp = parties(r.get("title"))
    return str(cnr), {
        "cnr": r.get("cnr"), "court": r.get("court"), "title": (r.get("title") or "")[:400],
        "petitioner": pet, "respondent": resp, "judge": r.get("judge"),
        "decision_date": str(r.get("decision_date"))[:10] if r.get("decision_date") else None,
        "disposal_nature": r.get("disposal_nature"), "pdf_link": r.get("pdf_link"),
    }

def row_case(r):
    """One case_details row -> (cnr, data): structured parties + advocates + acts."""
    if not r.get("cnr"): return None
    return str(r["cnr"]), {
        "cnr": r.get("cnr"), "case_no": r.get("case_no"), "case_type": r.get("case_type"),
        "court": r.get("court"), "bench": r.get("bench"), "judge": r.get("judge"),
        "petitioner": (r.get("petitioner") or None), "respondent": (r.get("respondent") or None),
        "pet_advocate": r.get("pet_advocate"), "res_advocate": r.get("res_advocate"),
        "date_of_decision": str(r.get("date_of_decision"))[:10] if r.get("date_of_decision") else None,
        "disposal_nature": r.get("disposal_nature"), "acts": r.get("acts"), "linked_cases": r.get("linked_cases"),
    }
