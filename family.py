"""What this family scrapes. Change this file first.

Family `court-judgments`: case METADATA for India's High Courts and the Supreme Court, from the public AWS Open Data buckets
(github.com/vanga, sponsored by AWS, readable with no credentials). We take the metadata parquet only — party names, judges,
dates, disposal, acts and advocates — not the 1.25 TB of judgment PDFs. One queue item = one parquet object.

Buckets (region ap-south-1, unsigned reads):
  indian-high-court-judgments     metadata/parquet/ (per year/court/bench) and metadata/parquet_case_details/ (sparse, richer)
  indian-supreme-court-judgments  metadata/parquet/ (per year)
"""
import json
from pathlib import Path

import boto3
from botocore import UNSIGNED
from botocore.client import Config

FAMILY = json.loads((Path(__file__).parent / "scrape.json").read_text())["family"]
HC = "indian-high-court-judgments"
SC = "indian-supreme-court-judgments"


def _s3():
    return boto3.client("s3", region_name="ap-south-1", config=Config(signature_version=UNSIGNED))


def _list(bucket, prefix):
    """All .parquet object keys under a prefix."""
    out = []
    for page in _s3().get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for o in page.get("Contents", []):
            if o["Key"].endswith(".parquet"):
                out.append(o["Key"])
    return out


def _court(key):
    """Court code from a partition path like year=2023/court=10_8/bench=... -> '10_8'."""
    for part in key.split("/"):
        if part.startswith("court="):
            return part[6:]
    return None


def items(bucket, prefix, kind):
    """One queue item per parquet object. key = the object key (stable, unique)."""
    return [{"key": k, "payload": {"bucket": bucket, "key": k, "kind": kind, "court": _court(k), "expected": 300}}
            for k in _list(bucket, prefix)]


PROJECTS = [
    {"name": f"{FAMILY}-hc", "title": "High Court case metadata", "task": "meta",
     "target": f"{HC}.s3", "env": {}, "max_workers": 20,
     "unit_label": "parquet file", "record_label": "case",
     "bucket": HC, "prefix": "metadata/parquet/", "kind": "meta"},
    {"name": f"{FAMILY}-hc-cases", "title": "High Court case details (parties, advocates, acts)", "task": "meta",
     "target": f"{HC}.s3", "env": {}, "max_workers": 8,
     "unit_label": "parquet file", "record_label": "case",
     "bucket": HC, "prefix": "metadata/parquet_case_details/", "kind": "case"},
    {"name": f"{FAMILY}-sc", "title": "Supreme Court case metadata", "task": "meta",
     "target": f"{SC}.s3", "env": {}, "max_workers": 8,
     "unit_label": "parquet file", "record_label": "case",
     "bucket": SC, "prefix": "metadata/parquet/", "kind": "meta"},
]
