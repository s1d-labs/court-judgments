"""Pure-parser tests: title -> parties, and the two row mappers. No network."""
import parse

def test_parties_with_case_prefix():
    assert parse.parties("CR. MISC./68032/2022 of MAMTA DEVI Vs The State of Bihar") == ("MAMTA DEVI", "The State of Bihar")

def test_parties_plain_and_variants():
    assert parse.parties("ABC Ltd versus XYZ")[0] == "ABC Ltd"
    assert parse.parties("A v/s B") == ("A", "B")
    assert parse.parties("Only One Name")[1] is None
    assert parse.parties("") == (None, None)

def test_row_meta():
    cnr, d = parse.row_meta({"cnr": "BRHC01", "court": "Patna High Court", "title": "X/1/2 of FOO PVT LTD Vs State",
                             "judge": "J", "decision_date": "2024-05-03 00:00:00", "disposal_nature": "ALLOWED"})
    assert cnr == "BRHC01" and d["petitioner"] == "FOO PVT LTD" and d["respondent"] == "State"
    assert d["decision_date"] == "2024-05-03" and d["disposal_nature"] == "ALLOWED"

def test_row_case_keeps_structured_parties_and_advocates():
    cnr, d = parse.row_case({"cnr": "HCBM05", "petitioner": "MARINETECH", "respondent": "MERINO INNOVATION PVT. LTD",
                             "pet_advocate": "SARDESSAI", "acts": "[{'act': 'ARBITRATION'}]", "date_of_decision": "2026-04-17"})
    assert cnr == "HCBM05" and d["respondent"].startswith("MERINO") and d["pet_advocate"] == "SARDESSAI"

def test_no_cnr_dropped():
    assert parse.row_case({"petitioner": "X"}) is None
