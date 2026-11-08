"""Put this family's projects in the pool and seed one queue item per AWS parquet object. Run by the Setup workflow.
Safe to run again: items that exist are kept. Reads the public buckets with no credentials."""
from scrape_hub_client import register_project, seed_queue, set_pool

from family import FAMILY, PROJECTS, items

for p in PROJECTS:
    its = items(p["bucket"], p["prefix"], p["kind"])
    register_project(p["name"], title=p["title"], unit_label=p["unit_label"], record_label=p["record_label"],
                     expected_units=len(its), expected_records=sum(i["payload"].get("expected", 0) for i in its))
    set_pool(p["name"], FAMILY, p["task"], target=p["target"], env=p["env"], max_workers=p.get("max_workers"))
    print(p["name"], "queue:", seed_queue(p["name"], its))
