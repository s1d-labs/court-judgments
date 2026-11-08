# court-judgments

High Court + Supreme Court case **metadata** for the s1d-labs pool, from the public AWS Open Data buckets published by
github.com/vanga (`indian-high-court-judgments`, `indian-supreme-court-judgments`; readable with no credentials, region
ap-south-1). We take the metadata parquet only — not the 1.25 TB of judgment PDFs.

## Projects
| Project | Source | Record (id = `cnr`) |
|---|---|---|
| `court-judgments-hc` | `metadata/parquet/` (per year/court/bench) | court, title, **petitioner/respondent** (parsed from the title), judge, decision date, disposal, pdf_link |
| `court-judgments-hc-cases` | `metadata/parquet_case_details/` (sparse, richer) | structured petitioner/respondent, **pet/res advocate**, acts, linked_cases, dates |
| `court-judgments-sc` | Supreme Court `metadata/parquet/` (per year) | as hc |

One queue item = one parquet object (`meta.py` downloads it unsigned, parses, stores one record per case). ~17.8M HC cases.

## Running
- `python -m pytest tests` — parser tests, no network.
- `python meta.py --local <bucket> <parquet-key> [meta|case]` — one file, no hub.
- `scrape-check --items 2` — setup + task on a local stand-in hub.

## Notes
- No geo/proxy: AWS Open Data is global and open. We never fetch the PDFs (`data/tar/`, 1.25 TB).
- Party names in `metadata/parquet` come from the title string; `case_details` has them as clean columns but covers few benches.
