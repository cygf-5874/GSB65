#!/usr/bin/env bash
# 固定验收入口：colfmt 的 11 个场景（width 3 + wrap 3 + align 2 + edge 2 + perf 1）。
# 用法：bash scripts/check.sh [-list] [--only <组名>]
set -uo pipefail

cd "$(dirname "$0")/.."
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for candidate in python3 python py; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PY="$candidate"
      break
    fi
  done
fi

if [ -z "$PY" ]; then
  echo "找不到 Python 解释器（python3 / python / py）" >&2
  exit 2
fi

exec "$PY" check.py "$@"
