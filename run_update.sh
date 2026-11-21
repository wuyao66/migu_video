#!/bin/bash
# 单次运行封装：抓取 -> 排序 -> 写心跳
# 任何一步失败或频道数异常，立即删除半成品，保证仓库里的旧 m3u 不被覆盖成残缺文件
set -uo pipefail

START_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
START_EPOCH=$(date -u +%s)
LOG="migu_run.log"

echo "==== run start: ${START_ISO} ===="
echo "soft deadline: 480s / step limit: 12min"

python3 MIGU.py > "${LOG}" 2>&1
RC_MIGU=$?
echo "MIGU.py exit=${RC_MIGU}"
tail -n 40 "${LOG}" || true

python3 sort_m3u.py >> "${LOG}" 2>&1
RC_SORT=$?
echo "sort_m3u.py exit=${RC_SORT}"
tail -n 15 "${LOG}" || true

CHANNELS=$(grep -c '^#EXTINF' migu.m3u 2>/dev/null || true)
CHANNELS=${CHANNELS:-0}
echo "channels=${CHANNELS}"

if [ "${RC_MIGU}" -ne 0 ] || [ "${RC_SORT}" -ne 0 ] || [ "${CHANNELS}" -lt 30 ]; then
  echo "!! 生成失败 (migu=${RC_MIGU} sort=${RC_SORT} channels=${CHANNELS})，删除半成品，保留仓库旧文件"
  rm -f migu.m3u cctv.migu.m3u
  python3 write_heartbeat.py "${START_ISO}" "${START_EPOCH}" "${RC_MIGU}" "${RC_SORT}" || true
  echo "::error::migu 生成失败 rc_migu=${RC_MIGU} rc_sort=${RC_SORT} channels=${CHANNELS}"
  exit 1
fi

python3 write_heartbeat.py "${START_ISO}" "${START_EPOCH}" "${RC_MIGU}" "${RC_SORT}" || true
echo "==== run done: channels=${CHANNELS} ===="
exit 0
