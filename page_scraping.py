#!/usr/bin/env python3
import argparse
import csv
import json
import random
import sys
import time
from typing import Any, Dict, List, Optional

import requests

X_IG_APP_ID = "936619743392459"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}


def get_instagram_metadata(
    username: str,
    *,
    session: Optional[requests.Session] = None,
    timeout_s: int = 15,
    max_retries: int = 3,
) -> Dict[str, Any]:
    api = "https://www.instagram.com/api/v1/users/web_profile_info/"
    params = {"username": username}

    headers = dict(DEFAULT_HEADERS)
    headers["X-IG-App-ID"] = X_IG_APP_ID
    headers["Referer"] = f"https://www.instagram.com/{username}/"

    s = session or requests.Session()

    for attempt in range(max_retries + 1):
        r = s.get(api, params=params, headers=headers, timeout=timeout_s, allow_redirects=False)

        if r.status_code in (301, 302, 303, 307, 308):
            loc = r.headers.get("Location", "")
            raise RuntimeError(f"{username}: redirected (likely login/consent required): {loc}")

        if r.status_code == 429:
            retry_after = r.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                sleep_s = int(retry_after)
            else:
                sleep_s = (2 ** attempt) + random.random()
            time.sleep(sleep_s)
            continue

        r.raise_for_status()
        j = r.json()

        user = (j.get("data") or {}).get("user") or j.get("user")
        if not user:
            raise RuntimeError(f"{username}: unexpected response structure: keys={list(j.keys())}")

        return {
            "id": user.get("id"),
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "biography": user.get("biography"),
            "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url"),
            "followers": (user.get("edge_followed_by") or {}).get("count"),
            "following": (user.get("edge_follow") or {}).get("count"),
            "posts": (user.get("edge_owner_to_timeline_media") or {}).get("count"),
            "is_private": user.get("is_private"),
            "is_verified": user.get("is_verified"),
        }

    raise RuntimeError(f"{username}: failed after retries (repeated 429 or transient errors)")


def read_usernames_from_file(path: str) -> List[str]:
    names: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            u = line.strip()
            if not u or u.startswith("#"):
                continue
            # allow full urls too
            u = u.replace("https://www.instagram.com/", "").strip("/")
            names.append(u)
    return names


def write_csv(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    fieldnames = sorted({k for row in rows for k in row.keys()})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch Instagram public profile metadata (low volume).")
    p.add_argument("usernames", nargs="*", help="Instagram usernames (e.g., instagram natgeo).")
    p.add_argument("-f", "--file", help="Text file with usernames (one per line).")
    p.add_argument("--json-out", help="Write full results to a JSON file.")
    p.add_argument("--csv-out", help="Write results to a CSV file.")
    p.add_argument("--sleep", type=float, default=5.0, help="Seconds to sleep between profiles (default: 5).")
    p.add_argument("--timeout", type=int, default=5, help="HTTP timeout seconds (default: 15).")
    p.add_argument("--retries", type=int, default=3, help="Max retries on 429/transient errors (default: 3).")
    args = p.parse_args()

    usernames: List[str] = []
    usernames.extend(args.usernames)
    if args.file:
        usernames.extend(read_usernames_from_file(args.file))

    seen = set()
    usernames = [u for u in usernames if not (u in seen or seen.add(u))]

    if not usernames:
        p.print_help()
        return 2

    results: List[Dict[str, Any]] = []
    with requests.Session() as s:
        for i, u in enumerate(usernames, start=1):
            try:
                data = get_instagram_metadata(
                    u,
                    session=s,
                    timeout_s=args.timeout,
                    max_retries=args.retries,
                )
                results.append(data)
                print(json.dumps(data, ensure_ascii=False))
            except Exception as e:
                print(f"ERROR: {e}", file=sys.stderr)

            if i < len(usernames):
                time.sleep(max(0.0, args.sleep))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    if args.csv_out:
        write_csv(args.csv_out, results)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
