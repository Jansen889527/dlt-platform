#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大乐透开奖数据自动更新脚本（本机 / GitHub Actions 通用）
=======================================================
1. 从 500 彩票网抓取最近 120 期真实开奖（复用根目录 dlt_live.py 的抓取与解析）
2. 若出现新一期：
   - 更新 data.json
   - 更新 index.html 里的内置 FALLBACK 快照
   - 同步 android-app/www/ 与 assets/public/ 两份离线快照
   - 自动 bump version.json / index.html 的 APP_VERSION / sw.js 缓存名
     → 已安装 App 的用户点「检查更新」会收到「发现新版本」提示
3. 没有新期则什么都不改（Actions 里不会产生空提交）

用法：
    python3 scripts/update_dlt_data.py
退出码 0 表示成功（含"无新期"），非 0 表示抓取/解析失败。
"""
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import dlt_live  # noqa: E402

# 网页副本：根目录之外需要同步的两处（离线快照）
COPIES = [
    ROOT / "android-app" / "www",
    ROOT / "android-app" / "android" / "app" / "src" / "main" / "assets" / "public",
]
WEB_FILES = ["index.html", "data.json", "version.json", "sw.js"]


def compact(data):
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def bump(version):
    """2026.11.5 -> 2026.11.6"""
    parts = version.split(".")
    try:
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)
    except (ValueError, IndexError):
        return version + ".1"


def replace_one(text, pattern, repl, label):
    new, n = re.subn(pattern, lambda m: repl, text, count=1, flags=re.M)
    if n != 1:
        raise RuntimeError("替换失败: " + label)
    return new


def main():
    html = dlt_live.fetch_html(dlt_live.HIST_URL)
    data = dlt_live.parse(html)
    if len(data) < 20:
        raise RuntimeError("解析期数过少(%d)，数据源可能改版，放弃更新" % len(data))

    new_code = data[0]["code"]
    data_path = ROOT / "data.json"
    old = json.loads(data_path.read_text(encoding="utf-8"))
    old_code = old[0]["code"]

    if int(new_code) <= int(old_code):
        print("NO_CHANGE 当前已是最新 %s (%s)" % (old_code, old[0]["date"]))
        return 0

    print("NEW_ISSUE %s (%s) <- 旧数据 %s (%s)" %
          (new_code, data[0]["date"], old_code, old[0]["date"]))

    # ---- 版本号 ----
    vp = ROOT / "version.json"
    vinfo = json.loads(vp.read_text(encoding="utf-8"))
    new_ver = bump(vinfo.get("version", "2026.11.5"))
    vinfo["version"] = new_ver
    vinfo["note"] = "开奖数据同步至 %s（500彩票网）" % new_code
    vinfo["updatedAt"] = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    vp.write_text(json.dumps(vinfo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ---- data.json ----
    data_path.write_text(compact(data) + "\n", encoding="utf-8")

    # ---- index.html：FALLBACK 快照 + APP_VERSION + 注释里的更新说明 ----
    ip = ROOT / "index.html"
    idx = ip.read_text(encoding="utf-8")
    idx = replace_one(idx, r"^const FALLBACK = \[.*\];$",
                      "const FALLBACK = " + compact(data) + ";", "FALLBACK")
    idx = replace_one(idx, r"var APP_VERSION = '[^']+';",
                      "var APP_VERSION = '%s';" % new_ver, "APP_VERSION")
    ip.write_text(idx, encoding="utf-8")

    # ---- sw.js：换缓存名，避免老用户读到旧数据 ----
    sp = ROOT / "sw.js"
    sw = sp.read_text(encoding="utf-8")
    m = re.search(r"const CACHE = '([^']+)';", sw)
    if not m:
        raise RuntimeError("sw.js 未找到 CACHE 常量")
    old_cache = m.group(1)
    cm = re.search(r"^(.*?)(\d+)$", old_cache)
    new_cache = (cm.group(1) + str(int(cm.group(2)) + 1)) if cm else old_cache + "-2"
    sw = sw.replace("const CACHE = '%s';" % old_cache,
                    "const CACHE = '%s';" % new_cache, 1)
    sp.write_text(sw, encoding="utf-8")

    # ---- 同步两份离线快照（目录存在才写）----
    for d in COPIES:
        if not d.is_dir():
            continue
        for f in WEB_FILES:
            (d / f).write_bytes((ROOT / f).read_bytes())

    print("UPDATED version=%s cache=%s 期数=%d 最新=%s/%s" %
          (new_ver, new_cache, len(data), new_code, data[0]["date"]))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("ERROR %s: %s" % (type(e).__name__, e), file=sys.stderr)
        sys.exit(1)
