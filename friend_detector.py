import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


def load_json_or_csv(path: str) -> List[Dict[str, Any]]:
    """Load friend list from JSON or CSV."""
    ext = os.path.splitext(path)[1].lower()

    if ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [item if isinstance(item, dict) else {"value": item} for item in data]
        if isinstance(data, dict):
            return [data]
        raise ValueError(f"Unsupported JSON structure in {path}")

    if ext == ".csv":
        if pd is None:
            raise RuntimeError("pandas is required to read CSV. Install requirements.txt first.")
        df = pd.read_csv(path)
        return df.to_dict(orient="records")

    raise ValueError(f"Unsupported file type: {path}")


def normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a friend record to stable key/value pairs."""
    normalized: Dict[str, Any] = {}
    for key, value in record.items():
        normalized[str(key).strip()] = value
    return normalized


def get_identity(record: Dict[str, Any]) -> str:
    """Return a unique identity string for the friend.

    Preferred order: username, wxid, id, nickname + remark.
    """
    candidates = [
        record.get("username"),
        record.get("wxid"),
        record.get("id"),
        record.get("user_id"),
        record.get("open_id"),
        record.get("account"),
    ]

    for cand in candidates:
        if cand is not None and str(cand).strip() != "":
            return str(cand).strip()

    # fallback: build a deterministic key from common fields
    nickname = str(record.get("nickname") or "").strip()
    remark = str(record.get("remark") or "").strip()
    return f"{nickname}|{remark}" if nickname or remark else json.dumps(record, ensure_ascii=False)


def build_index(records: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for rec in records:
        norm = normalize_record(rec)
        identity = get_identity(norm)
        index[identity] = norm
    return index


def compare_friends(before_path: str, after_path: str) -> Dict[str, Any]:
    before_records = load_json_or_csv(before_path)
    after_records = load_json_or_csv(after_path)

    before_map = build_index(before_records)
    after_map = build_index(after_records)

    before_ids = set(before_map.keys())
    after_ids = set(after_map.keys())

    deleted_ids = sorted(before_ids - after_ids)
    added_ids = sorted(after_ids - before_ids)

    deleted = [before_map[i] for i in deleted_ids]
    added = [after_map[i] for i in added_ids]

    result = {
        "deleted": deleted,
        "added": added,
        "deleted_count": len(deleted),
        "added_count": len(added),
        "unchanged_count": len(before_ids & after_ids),
        "before_file": before_path,
        "after_file": after_path,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return result


def monitor_directory(folder: str, pattern: str = "*.json", interval: int = 10, output_path: Optional[str] = None):
    """Monitor a folder for JSON snapshots and compare the newest two files.

    This is a very lightweight local demo; in production you would likely use
    a scheduler or watch service.
    """
    import time

    files = []
    while True:
        current = []
        for name in os.listdir(folder):
            if name.endswith(".json") or pattern in ("*.json", "*.csv"):
                if name.lower().endswith((".json", ".csv")):
                    current.append(os.path.join(folder, name))
        current.sort()

        if len(current) >= 2:
            newer = current[-1]
            older = current[-2]
            result = compare_friends(older, newer)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            break

        time.sleep(interval)


def parse_args():
    parser = argparse.ArgumentParser(description="Compare WeChat friend snapshots and detect changes.")
    parser.add_argument("--before", help="Path to the older snapshot file.")
    parser.add_argument("--after", help="Path to the newer snapshot file.")
    parser.add_argument("--output", help="Optional output JSON path for the comparison report.")
    parser.add_argument("--watch", help="Directory to monitor for file updates.")
    parser.add_argument("--pattern", default="*.json", help="File glob pattern when watching a directory.")
    parser.add_argument("--interval", type=int, default=10, help="Polling interval in seconds for --watch.")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.watch:
        monitor_directory(args.watch, args.pattern, args.interval, args.output)
        return

    if not args.before or not args.after:
        raise SystemExit("Please provide both --before and --after, or use --watch.")

    result = compare_friends(args.before, args.after)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
