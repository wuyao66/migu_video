#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每次运行必写 last_run.json —— 用于判断「到底有没有每小时跑」。

用法：write_heartbeat.py <start_iso> <start_epoch> <rc_migu> <rc_sort>
退出码恒为 0，不干扰主流程。
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

M3U = "migu.m3u"
CCTV = "cctv.migu.m3u"
LOG = "migu_run.log"
OUT = "last_run.json"
MIN_CHANNELS = 30  # 低于该值视为生成失败


def count_channels(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.startswith("#EXTINF:"))
    except FileNotFoundError:
        return 0


def parse_log(path):
    failed, retried, ok = [], 0, 0
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "更新失败" in line:
                    failed.append(line.strip())
                elif "次请求失败" in line:
                    retried += 1
                elif "更新成功" in line:
                    ok += 1
    except FileNotFoundError:
        pass
    return failed, retried, ok


def main():
    start_iso = sys.argv[1] if len(sys.argv) > 1 else ""
    start_epoch = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    rc_migu = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    rc_sort = int(sys.argv[4]) if len(sys.argv) > 4 else 0

    channels = count_channels(M3U)
    cctv = count_channels(CCTV)
    failed, retried, ok = parse_log(LOG)

    if rc_migu != 0 or rc_sort != 0 or channels < MIN_CHANNELS:
        status = "failed"
    elif failed:
        status = "degraded"
    else:
        status = "ok"

    now = datetime.now(timezone.utc)
    payload = {
        "last_run_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_run_cst": now.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "channels": channels,
        "cctv_channels": cctv,
        "ok_channels": ok,
        "failed_channels": len(failed),
        "retries": retried,
        "duration_sec": round(time.time() - start_epoch, 1) if start_epoch else None,
        "exit_code_migu": rc_migu,
        "exit_code_sort": rc_sort,
        "run_start": start_iso,
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
