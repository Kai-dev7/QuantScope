#!/usr/bin/env python3
"""Backfill user_id/user on analysis_reports from matching analysis_tasks.

Run inside the backend environment:
    python scripts/migrations/backfill_analysis_report_user_ids.py
"""

import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from pymongo import MongoClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _load_dotenv() -> None:
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _replace_mongodb_host_for_host_runtime(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.hostname != "mongodb":
        return uri

    try:
        socket.getaddrinfo("mongodb", parsed.port or 27017)
        return uri
    except socket.gaierror:
        pass

    netloc = parsed.netloc.replace("@mongodb:", "@localhost:").replace("mongodb:", "localhost:", 1)
    return urlunparse(parsed._replace(netloc=netloc))


def get_db():
    _load_dotenv()

    raw_uri = (
        os.getenv("MONGO_URI")
        or os.getenv("MONGODB_URL")
        or os.getenv("MONGODB_CONNECTION_STRING")
        or "mongodb://localhost:27017/tradingagents"
    )
    mongo_uri = _replace_mongodb_host_for_host_runtime(raw_uri)
    database_name = os.getenv("MONGODB_DATABASE") or os.getenv("MONGODB_DATABASE_NAME") or "tradingagents"

    print(f"Using MongoDB URI: {mongo_uri.replace(os.getenv('MONGODB_PASSWORD', ''), '***') if os.getenv('MONGODB_PASSWORD') else mongo_uri}")
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client[database_name]


def main() -> None:
    db = get_db()
    updated = 0
    skipped = 0

    reports = db.analysis_reports.find(
        {
            "$and": [
                {"$or": [{"user_id": {"$exists": False}}, {"user_id": None}]},
                {"$or": [{"task_id": {"$exists": True, "$ne": ""}}, {"analysis_id": {"$exists": True, "$ne": ""}}]},
            ]
        },
        {"task_id": 1, "analysis_id": 1},
    )

    for report in reports:
        task_query = {"$or": []}
        if report.get("task_id"):
            task_query["$or"].append({"task_id": report["task_id"]})
        if report.get("analysis_id"):
            task_query["$or"].append({"result.analysis_id": report["analysis_id"]})

        task = db.analysis_tasks.find_one(task_query, {"user_id": 1, "user": 1})
        report_user_id = task.get("user_id", task.get("user")) if task else None

        if report_user_id is None:
            skipped += 1
            continue

        db.analysis_reports.update_one(
            {"_id": report["_id"]},
            {"$set": {"user_id": report_user_id, "user": report_user_id}},
        )
        updated += 1

    print(f"Backfill complete: updated={updated}, skipped={skipped}")


if __name__ == "__main__":
    main()
