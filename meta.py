#!/usr/bin/env python3
"""The `meta` task: read one AWS Open Data court-metadata parquet and store one record per case.

Source: the public, no-sign-in buckets from github.com/vanga —
  indian-high-court-judgments  (metadata/parquet, metadata/parquet_case_details)
  indian-supreme-court-judgments (metadata/parquet)
We take only the METADATA (party names are in the title / petitioner / respondent, plus judge, dates, disposal, acts and
advocates where present). We do NOT download the 1.25 TB of judgment PDFs. One queue item = one parquet object; its payload is
{bucket, key, kind}. kind 'meta' = a metadata/parquet file (title -> parties); 'case' = a case_details file (structured parties).

Try one file without the hub:  python meta.py --local indian-high-court-judgments metadata/parquet/year=2023/.../metadata.parquet meta
"""
import io
import os
import sys
import time

import boto3
from botocore import UNSIGNED
from botocore.client import Config
import pyarrow.parquet as pq

import parse

REGION = os.environ.get("AWS_S3_REGION", "ap-south-1")
DEADLINE = time.time() + float(os.environ.get("SCRAPE_MAX_HOURS", "1")) * 3600 - 180


def s3():
    return boto3.client("s3", region_name=REGION, config=Config(signature_version=UNSIGNED, max_pool_connections=16))


def read_rows(bucket, key):
    body = s3().get_object(Bucket=bucket, Key=key)["Body"].read()
    return pq.read_table(io.BytesIO(body)).to_pylist()


def do_item(hub, item):
    p = item["payload"]
    rows = read_rows(p["bucket"], p["key"])
    fn = parse.row_case if p.get("kind") == "case" else parse.row_meta
    n = 0
    seen = set()
    for r in rows:
        out = fn(r)
        if not out:
            continue
        rid, data = out
        if rid in seen:                       # one parquet can repeat a cnr across order rows; keep the first
            continue
        seen.add(rid)
        data["src_court"] = p.get("court")
        hub.record(rid, data)
        n += 1
    return n


def main():
    from scrape_hub_client import HubClient
    hub = HubClient(os.environ.get("SCRAPE_POOL_PROJECT", ""),
                    job_index=int(os.environ.get("SCRAPE_JOB_INDEX", "0")),
                    total_jobs=int(os.environ.get("SCRAPE_TOTAL_JOBS", "1")))
    try:
        while time.time() < DEADLINE:
            if hub.settings.get("paused"):
                time.sleep(30); continue
            items = hub.claim(1, steal=True, retry_failed=True)
            if not items:
                break
            it = items[0]
            try:
                n = do_item(hub, it)
                hub.complete([it["key"]], "done", fetched=n)
            except Exception as e:  # noqa: BLE001
                hub.complete([it["key"]], "failed", error=f"{type(e).__name__}: {e}"[:200])
        hub.close()
    except BaseException as e:
        hub.close("failed", f"{type(e).__name__}: {e}"[:200])
        raise


class LocalHub:
    settings = {"paused": False}

    def __init__(self):
        self.n = 0

    def record(self, rid, data):
        self.n += 1
        if self.n <= 4:
            import json
            print(json.dumps({"record_id": rid, "data": data}, ensure_ascii=False, default=str))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--local"]:
        hub = LocalHub()
        n = do_item(hub, {"payload": {"bucket": sys.argv[2], "key": sys.argv[3], "kind": sys.argv[4] if len(sys.argv) > 4 else "meta"}})
        print(f"{n} records", file=sys.stderr)
    else:
        main()
