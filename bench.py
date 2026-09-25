#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""colfmt 的性能入口：渲染一张 1000 行 × 12 列的混排表并打印耗时。

用法：
    python3 bench.py            # 默认 1000 行
    python3 bench.py 3000       # 指定行数

性能判据是**按本机标定**的（见 README「对外契约」第 11 条）：本机一份满足全部契约的
实现渲染 1000 行 × 12 列约 0.03 s 量级，`check.py` 的 `perf` 组把上限写死在
`PERF_SECONDS = 1.0`。跑题机更慢时按比例放宽。

本文件是固定件，**不要修改**。
"""

import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:  # pragma: no cover
    pass

COLUMNS = 12
WIDTH = 8
WORDS = [
    "编号",
    "名称",
    "值",
    "说明",
    "宽",
    "备注",
    "标签",
    "数据",
    "漢字",
    "表格",
    "渲染",
    "对齐",
]


def make_rows(count):
    return [
        [WORDS[(i + j) % len(WORDS)] + str(i % 97) + "ab" for j in range(COLUMNS)]
        for i in range(count)
    ]


def main(argv):
    rows_count = 1000
    if len(argv) >= 1:
        rows_count = int(argv[0])

    from colfmt import render_table

    rows = make_rows(rows_count)
    start = time.perf_counter()
    text = render_table(rows, widths=[WIDTH] * COLUMNS)
    elapsed = time.perf_counter() - start

    print("行数           = %d" % rows_count)
    print("列数           = %d" % COLUMNS)
    print("输出行数       = %d" % (text.count("\n") + 1))
    print("输出字节数     = %d" % len(text.encode("utf-8")))
    print("渲染耗时       = %.4f s" % elapsed)
    print("（按本机标定：check.py 的 perf 组上限为 1.0 s，跑题机更慢时按比例放宽）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
