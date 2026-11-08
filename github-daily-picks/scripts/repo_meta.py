#!/usr/bin/env python3
"""核准指定仓库的真实元数据，输出 markdown 表格。

写卡片前必须跑一遍，禁止凭记忆写 stars。

用法:
    python repo_meta.py ultralytics/ultralytics RVC-Project/Retrieval-based-Voice-Conversion-WebUI

可选环境变量:
    GITHUB_TOKEN  提升 API 限流额度（未登录：核心接口 60 次/小时）
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

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
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    token = os.environ.get("GITHUB_TOKEN")
    rows = []

    for full in sys.argv[1:]:
        full = full.strip().strip("/")
        try:
            d = get(f"{API}/repos/{full}", token)
        except urllib.error.HTTPError as e:
            print(f"[失败] {full}: HTTP {e.code}", file=sys.stderr)
            rows.append({"repo": full, "stars": "查询失败", "language": "-",
                         "license": "-", "pushed": "-", "archived": "-",
                         "topics": "-", "url": f"https://github.com/{full}"})
            continue

        rows.append({
            "repo": d["full_name"],
            "stars": d["stargazers_count"],
            "forks": d["forks_count"],
            "language": d.get("language") or "-",
            "license": (d.get("license") or {}).get("spdx_id") or "NOASSERTION",
            "pushed": d["pushed_at"][:10],
            "created": d["created_at"][:10],
            "archived": "是" if d.get("archived") else "否",
            "issues": d["open_issues_count"],
            "size_mb": round(d.get("size", 0) / 1024, 1),
            "homepage": d.get("homepage") or "-",
            "topics": ", ".join(d.get("topics") or []) or "-",
            "description": (d.get("description") or "").replace("|", "/"),
            "url": d["html_url"],
        })

    print("| 仓库 | Stars | Forks | 语言 | 协议 | 最近提交 | 归档 | 链接 |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['repo']} | {r['stars']} | {r.get('forks', '-')} | {r['language']} "
              f"| {r['license']} | {r['pushed']} | {r['archived']} | {r['url']} |")

    print("\n补充信息：")
    for r in rows:
        if r["stars"] == "查询失败":
            continue
        print(f"- {r['repo']}")
        print(f"  简介: {r['description'] or '(无描述)'}")
        print(f"  创建: {r['created']} ｜ 未关 issue: {r['issues']} ｜ 仓库体积: {r['size_mb']} MB")
        print(f"  主题: {r['topics']}")
        print(f"  主页: {r['homepage']}")


if __name__ == "__main__":
    main()
