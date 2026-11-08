#!/usr/bin/env python3
"""按关键词搜索 GitHub 仓库并按硬门槛过滤，输出 markdown 表格。

用法:
    python search_repos.py --query "video subtitle remover" --query "video super resolution"
    python search_repos.py --query "self hosted" --min-stars 500 --months 12 --limit 8

可选环境变量:
    GITHUB_TOKEN  提升 API 限流额度（未登录：搜索 10 次/分钟）
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://api.github.com"
UA = "github-daily-picks-skill/1.0"


def get(url, token=None, retries=3):
    last = None
    for attempt in range(retries):
        req = urllib.request.Request(url)
        req.add_header("User-Agent", UA)
        req.add_header("Accept", "application/vnd.github+json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", action="append", required=True, help="搜索关键词，可重复")
    ap.add_argument("--min-stars", type=int, default=300)
    ap.add_argument("--months", type=int, default=12, help="最近 N 个月内有提交")
    ap.add_argument("--limit", type=int, default=6, help="每条 query 输出上限")
    ap.add_argument("--json", action="store_true", help="输出 JSON 而非表格")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.months * 30)
    seen, rows = set(), []

    for q in args.query:
        query = f"{q} stars:>={args.min_stars} fork:false archived:false"
        url = (f"{API}/search/repositories?q={urllib.parse.quote(query)}"
               f"&sort=stars&order=desc&per_page=30")
        try:
            data = get(url, token)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")[:300]
            print(f"[跳过] query={q!r} HTTP {e.code}: {body}", file=sys.stderr)
            continue

        kept = 0
        for item in data.get("items", []):
            full = item["full_name"]
            if full in seen:
                continue
            if item.get("fork") or item.get("archived"):
                continue
            pushed = datetime.strptime(
                item["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if pushed < cutoff:
                continue
            seen.add(full)
            lic = (item.get("license") or {}).get("spdx_id") or "NOASSERTION"
            rows.append({
                "full_name": full,
                "stars": item["stargazers_count"],
                "language": item.get("language") or "-",
                "license": lic,
                "pushed_at": pushed.strftime("%Y-%m-%d"),
                "description": (item.get("description") or "").replace("|", "/")[:110],
                "url": item["html_url"],
                "query": q,
            })
            kept += 1
            if kept >= args.limit:
                break

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    if not rows:
        print("没有命中硬门槛的候选。放宽关键词或降低 --min-stars。")
        return

    print(f"候选 {len(rows)} 个（stars>={args.min_stars}，{args.months} 个月内活跃，非 fork 非归档）\n")
    print("| 仓库 | Stars | 语言 | 协议 | 最近提交 | 简介 |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        print(f"| [{r['full_name']}]({r['url']}) | {r['stars']} | {r['language']} "
              f"| {r['license']} | {r['pushed_at']} | {r['description']} |")
    print("\n下一步：挑出入围者，用 repo_meta.py 核准最终数字。")


if __name__ == "__main__":
    main()
