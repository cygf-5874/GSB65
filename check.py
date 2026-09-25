#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""colfmt 的固定验收程序。

用法：
    python3 check.py                 # 跑全部 11 个场景
    python3 check.py -list           # 列出全部场景名
    python3 check.py --only width    # 只跑一组（width / wrap / align / edge / perf）

输出格式：
    逐场景 `PASS <组>/<名>` 或 `FAIL <组>/<名>  期望=… 实际=…`
    结尾 `结果：通过 x/N`；全过 exit 0，否则 exit 1。

每个场景在**独立子进程**里跑并带超时看门狗：某个场景卡死或崩溃不会遮蔽其余场景，
失败也不早退。

本文件是固定件，**不要修改**。改动它等于改动题目。
"""

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:  # pragma: no cover - 老解释器没有 reconfigure
    pass

# 性能组的时限（秒）。按本机标定：本机一份满足全部契约的实现实测 0.03 s 左右，
# 起点实现不是慢、而是「快但错」（对齐判据不过）。跑题机更慢时按比例放宽。
PERF_SECONDS = 1.0
PERF_ROWS = 1000
PERF_COLUMNS = 12
PERF_WIDTH = 8

SCENARIO_TIMEOUT = 30.0
PERF_TIMEOUT = 120.0


class Mismatch(Exception):
    def __init__(self, expected, actual):
        super().__init__("%s != %s" % (expected, actual))
        self.expected = expected
        self.actual = actual


def brief(value, limit=400):
    text = value if isinstance(value, str) else repr(value)
    text = text.replace("\n", "\\n").replace("\t", "\\t")
    if len(text) > limit:
        text = text[:limit] + "…"
    return text


def eq(label, actual, expected):
    if actual != expected:
        raise Mismatch("%s => %s" % (label, brief(expected)), "%s => %s" % (label, brief(actual)))


def ok(label, condition, expected, actual):
    if not condition:
        raise Mismatch("%s => %s" % (label, brief(expected)), "%s => %s" % (label, brief(actual)))


# ---------------------------------------------------------------------------
# 独立的宽度模型：只覆盖 check.py 自己用到的字符，取值来自契约第 1 条。
# 不调用被测代码的 display_width，避免自证。
# ---------------------------------------------------------------------------

_NON_ASCII_WIDTH = {
    "\u6c49": 2,  # 汉
    "\u5b57": 2,  # 字
    "\u6f22": 2,  # 漢
    "\u540d": 2,  # 名
    "\u79f0": 2,  # 称
    "\u503c": 2,  # 值
    "\u8bf4": 2,  # 说
    "\u660e": 2,  # 明
    "\u5bbd": 2,  # 宽
    "\u5907": 2,  # 备
    "\u6ce8": 2,  # 注
    "\u6807": 2,  # 标
    "\u7b7e": 2,  # 签
    "\u6570": 2,  # 数
    "\u636e": 2,  # 据
    "\u8868": 2,  # 表
    "\u683c": 2,  # 格
    "\u6e32": 2,  # 渲
    "\u67d3": 2,  # 染
    "\u5bf9": 2,  # 对
    "\u9f50": 2,  # 齐
    "\u7f16": 2,  # 编
    "\u53f7": 2,  # 号
    "\u8865": 2,  # 补
    "\u7edf": 2,  # 统
    "\u8ba1": 2,  # 计
    "\uff21": 2,  # Ａ
    "\u3002": 2,  # 。
    "\uff5e": 2,  # ～
    "\ud55c": 2,  # 한
    "\U0001f600": 2,  # 😀
    "\u00e9": 1,  # é（单码点，Ambiguous）
    "\u00b7": 1,  # ·
    "\u2014": 1,  # —
    "\u2713": 1,  # ✓
    "\u0301": 0,  # 组合尖音符
    "\u0308": 0,  # 组合分音符
}


def width_of(text):
    """check.py 自带的显示宽度，仅用于校验渲染结果的一致性。"""
    total = 0
    for ch in text:
        if ord(ch) < 0x80:
            total += 1
        else:
            total += _NON_ASCII_WIDTH[ch]
    return total


# ---------------------------------------------------------------------------
# 场景
# ---------------------------------------------------------------------------

LIGHT = "light"

WIDTH_TABLE_ASCII = [
    ("", 0),
    ("a", 1),
    ("abc", 3),
    (" ", 1),
    ("  ", 2),
    ("#-+", 3),
    ("a | b", 5),
]

WIDTH_TABLE_EAST_ASIAN = [
    ("\u6c49", 2),
    ("\u6c49\u5b57", 4),
    ("\uff21", 2),
    ("\u3002", 2),
    ("\uff5e", 2),
    ("\ud55c", 2),
    ("\u6c49a", 3),
    ("\u540d\u503c", 4),
]

WIDTH_TABLE_COMBINING = [
    ("\U0001f600", 2),
    ("\u00e9", 1),
    ("\u00b7", 1),
    ("\u2014", 1),
    ("\u2713", 1),
    ("e\u0301", 1),
    ("\u0301", 0),
    ("\u6f22\u0301", 2),
    ("\u6f22\u5b57\u0301", 4),
    ("e\u0301x", 2),
]


def _check_width_table(samples, display_width):
    for text, expected in samples:
        eq("display_width(%r)" % (text,), display_width(text), expected)


def scenario_width_ascii():
    import colfmt

    display_width = colfmt.display_width
    render_table = colfmt.render_table

    _check_width_table(WIDTH_TABLE_ASCII, display_width)

    # 契约 9：单元格内的 `|` 与换行按写死策略转义，且不破坏表格结构。
    eq(
        "render_table([[a|b]], headers=[c|d])",
        render_table([["a|b"]], headers=["c|d"]),
        "+------+\n| c\\|d |\n+------+\n| a\\|b |\n+------+",
    )
    eq(
        "render_table([[x\\ny]], headers=[h])",
        render_table([["x\ny"]], headers=["h"]),
        "+--------+\n| h      |\n+--------+\n| x<br>y |\n+--------+",
    )

    # 契约 7：`\t` 按相对单元格起点的 8 的倍数展开。
    eq(
        "render_table(tab)",
        render_table([["\tab"], ["a\tb"]], headers=["c"]),
        "+------------+\n"
        "| c          |\n"
        "+------------+\n"
        "|         ab |\n"
        "+------------+\n"
        "| a       b  |\n"
        "+------------+",
    )

    # 契约 4：light 边框。
    eq(
        "render_table(light)",
        render_table([["a", "b"], ["cc", "d"]], headers=["h", "i"], style=LIGHT),
        "\u250c\u2500\u2500\u2500\u2500\u252c\u2500\u2500\u2500\u2510\n"
        "\u2502 h  \u2502 i \u2502\n"
        "\u251c\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2524\n"
        "\u2502 a  \u2502 b \u2502\n"
        "\u251c\u2500\u2500\u2500\u2500\u253c\u2500\u2500\u2500\u2524\n"
        "\u2502 cc \u2502 d \u2502\n"
        "\u2514\u2500\u2500\u2500\u2500\u2534\u2500\u2500\u2500\u2518",
    )


def scenario_width_east_asian():
    import colfmt

    display_width = colfmt.display_width
    render_table = colfmt.render_table

    _check_width_table(WIDTH_TABLE_EAST_ASIAN, display_width)

    # 契约 5：CJK 与 ASCII 混排时竖线落在同一列（逐字节期望输出）。
    text = render_table(
        [["\u6c49", "a"], ["abc", "\u6c49\u5b57"]],
        headers=["\u540d", "\u503c"],
    )
    eq(
        "render_table(CJK mix)",
        text,
        "+-----+------+\n"
        "| \u540d  | \u503c   |\n"
        "+-----+------+\n"
        "| \u6c49  | a    |\n"
        "+-----+------+\n"
        "| abc | \u6c49\u5b57 |\n"
        "+-----+------+",
    )
    widths = {width_of(line) for line in text.split("\n")}
    ok("每行显示宽度必须一致", len(widths) == 1, "1 种宽度", "%d 种：%r" % (len(widths), sorted(widths)))


def scenario_width_combining_emoji():
    import colfmt

    display_width = colfmt.display_width
    render_table = colfmt.render_table

    _check_width_table(WIDTH_TABLE_COMBINING, display_width)

    # 契约 4 + 8：none 风格只以单个空格分隔，且不带行尾空格。
    eq(
        "render_table(none)",
        render_table([["\u00e9", "\U0001f600"], ["e\u0301x", "\u6c49"]], headers=["a", "b"], style="none"),
        "a  b\n\u00e9  \U0001f600\ne\u0301x \u6c49",
    )


def scenario_wrap_ascii():
    import colfmt

    wrap_text = colfmt.wrap_text
    render_table = colfmt.render_table

    eq("wrap_text('abcdefghij', 4)", wrap_text("abcdefghij", 4), ["abcd", "efgh", "ij"])
    eq("wrap_text('abcdefghij', 3)", wrap_text("abcdefghij", 3), ["abc", "def", "ghi", "j"])
    eq("wrap_text('abc', 5)", wrap_text("abc", 5), ["abc"])
    eq("wrap_text('', 4)", wrap_text("", 4), [""])
    eq("wrap_text('abcdefghij', 0)", wrap_text("abcdefghij", 0), ["abcdefghij"])

    text = render_table([["abcdefghij", "xy"]], widths=[4, 3])
    eq(
        "render_table(wrap ascii)",
        text,
        "+------+-----+\n"
        "| abcd | xy  |\n"
        "| efgh |     |\n"
        "| ij   |     |\n"
        "+------+-----+",
    )


def scenario_wrap_wide():
    import colfmt

    wrap_text = colfmt.wrap_text
    render_table = colfmt.render_table

    source = "\u6f22\u5b57\u6f22\u5b57\u6f22\u5b57"
    eq(
        "wrap_text(wide, 5)",
        wrap_text(source, 5),
        ["\u6f22\u5b57", "\u6f22\u5b57", "\u6f22\u5b57"],
    )
    eq(
        "wrap_text(wide, 6)",
        wrap_text(source, 6),
        ["\u6f22\u5b57\u6f22", "\u5b57\u6f22\u5b57"],
    )
    eq(
        "wrap_text(wide, 3)",
        wrap_text(source, 3),
        ["\u6f22", "\u5b57", "\u6f22", "\u5b57", "\u6f22", "\u5b57"],
    )
    # 单个单元的显示宽度本身就大于列宽 —— 只能整块占一行，绝不劈开。
    eq("wrap_text(wide, 1)", wrap_text("\u6f22\u5b57", 1), ["\u6f22", "\u5b57"])

    for limit in (5, 6, 3):
        lines = wrap_text(source, limit)
        eq("wrap(%d) 不得丢字或重复" % limit, "".join(lines), source)
        for line in lines:
            ok(
                "wrap(%d) 每行不得超过列宽" % limit,
                width_of(line) <= limit or len(line) == 1,
                "显示宽度 <= %d" % limit,
                "第 %r 行显示宽度 = %d" % (line, width_of(line)),
            )

    text = render_table(
        [["\u6f22\u5b57\u6f22\u5b57\u6f22\u5b57", "ok"]],
        headers=["\u540d", "t"],
        widths=[5, 2],
    )
    eq(
        "render_table(wrap wide)",
        text,
        "+-------+----+\n"
        "| \u540d    | t  |\n"
        "+-------+----+\n"
        "| \u6f22\u5b57  | ok |\n"
        "| \u6f22\u5b57  |    |\n"
        "| \u6f22\u5b57  |    |\n"
        "+-------+----+",
    )


def scenario_wrap_combining():
    import colfmt

    wrap_text = colfmt.wrap_text
    render_table = colfmt.render_table

    eq(
        "wrap_text(e+ACUTE x3, 2)",
        wrap_text("e\u0301e\u0301e\u0301", 2),
        ["e\u0301e\u0301", "e\u0301"],
    )
    eq("wrap_text(漢+ACUTE 字, 2)", wrap_text("\u6f22\u0301\u5b57", 2), ["\u6f22\u0301", "\u5b57"])
    eq("wrap_text(漢+ACUTE 字, 3)", wrap_text("\u6f22\u0301\u5b57", 3), ["\u6f22\u0301", "\u5b57"])
    eq("wrap_text(ab+ACUTE c, 2)", wrap_text("ab\u0301c", 2), ["ab\u0301", "c"])
    eq("wrap_text(a+DIALYTIKA+ACUTE b, 2)", wrap_text("a\u0308\u0301b", 2), ["a\u0308\u0301b"])

    for text, limit in (("e\u0301e\u0301e\u0301", 2), ("\u6f22\u0301\u5b57", 2), ("ab\u0301c", 2)):
        lines = wrap_text(text, limit)
        eq("wrap(%r) 不得丢字" % (text,), "".join(lines), text)
        for line in lines:
            # 组合序列不被拆开：行首不得是组合记号。
            ok(
                "wrap(%r) 行首不得是组合记号" % (text,),
                not (line and line[0] in ("\u0301", "\u0308")),
                "行首为基字符",
                "行首是组合记号：%r" % (line,),
            )

    eq(
        "render_table(wrap combining)",
        render_table([["e\u0301e\u0301e\u0301", "\u6f22\u0301\u5b57"]], widths=[2, 2]),
        "+----+----+\n"
        "| e\u0301e\u0301 | \u6f22\u0301 |\n"
        "| e\u0301  | \u5b57 |\n"
        "+----+----+",
    )


def scenario_align_basic():
    import colfmt

    render_table = colfmt.render_table

    table = [["a", "bb"], ["ccc", "d"]]
    headers = ["h", "i"]

    eq(
        "align=left",
        render_table(table, headers=headers, align="left"),
        "+-----+----+\n"
        "| h   | i  |\n"
        "+-----+----+\n"
        "| a   | bb |\n"
        "+-----+----+\n"
        "| ccc | d  |\n"
        "+-----+----+",
    )
    eq(
        "align=right",
        render_table(table, headers=headers, align="right"),
        "+-----+----+\n"
        "|   h |  i |\n"
        "+-----+----+\n"
        "|   a | bb |\n"
        "+-----+----+\n"
        "| ccc |  d |\n"
        "+-----+----+",
    )
    # 逐列对齐。
    eq(
        "align=[left,right]",
        render_table([["a", "b"], ["cc", "dd"]], align=["left", "right"]),
        "+----+----+\n"
        "| a  |  b |\n"
        "+----+----+\n"
        "| cc | dd |\n"
        "+----+----+",
    )


def scenario_align_center_residual():
    import colfmt

    render_table = colfmt.render_table

    # 契约 3：center 的余数差额分配给右侧。
    eq(
        "center gap=3",
        render_table([["ab"]], widths=[5], align="center"),
        "+-------+\n"
        "|  ab   |\n"
        "+-------+",
    )
    eq(
        "center gap=5",
        render_table([["x"]], widths=[6], align="center"),
        "+--------+\n"
        "|   x    |\n"
        "+--------+",
    )
    eq(
        "center auto",
        render_table([["a", "abc"], ["abcd", "ab"]], align="center"),
        "+------+-----+\n"
        "|  a   | abc |\n"
        "+------+-----+\n"
        "| abcd | ab  |\n"
        "+------+-----+",
    )


def scenario_edge_shapes():
    import colfmt

    render_table = colfmt.render_table

    eq("render_table([])", render_table([]), "")
    eq("render_table([], headers=[])", render_table([], headers=[]), "")
    eq(
        "render_table(无表头单行)",
        render_table([["a", "bb"]]),
        "+---+----+\n| a | bb |\n+---+----+",
    )
    eq(
        "render_table(只有表头)",
        render_table([], headers=["a", "b"]),
        "+---+---+\n| a | b |\n+---+---+",
    )
    eq(
        "render_table(空字符串单元格)",
        render_table([["", "z"], ["x", ""]]),
        "+---+---+\n|   | z |\n+---+---+\n| x |   |\n+---+---+",
    )


def scenario_edge_single_column():
    import colfmt

    render_table = colfmt.render_table

    eq(
        "单列带表头",
        render_table([["x"], ["yy"]], headers=["id"]),
        "+----+\n| id |\n+----+\n| x  |\n+----+\n| yy |\n+----+",
    )
    eq("单列单行", render_table([["only"]]), "+------+\n| only |\n+------+")
    eq("单列只有表头", render_table([], headers=["only"]), "+------+\n| only |\n+------+")

    for text in (
        render_table([["x"], ["yy"]], headers=["id"]),
        render_table([["only"]]),
    ):
        for line in text.split("\n"):
            ok("不得有行尾空格", not line.endswith(" "), "行尾无空格", "行尾有空格：%r" % (line,))


WORDS = [
    "\u7f16\u53f7",
    "\u540d\u79f0",
    "\u503c",
    "\u8bf4\u660e",
    "\u5bbd",
    "\u5907\u6ce8",
    "\u6807\u7b7e",
    "\u6570\u636e",
    "\u6f22\u5b57",
    "\u8868\u683c",
    "\u6e32\u67d3",
    "\u5bf9\u9f50",
]


def scenario_perf_large():
    import colfmt

    rows = [
        [WORDS[(i + j) % len(WORDS)] + str(i % 97) + "ab" for j in range(PERF_COLUMNS)]
        for i in range(PERF_ROWS)
    ]

    start = time.perf_counter()
    text = colfmt.render_table(rows, widths=[PERF_WIDTH] * PERF_COLUMNS)
    elapsed = time.perf_counter() - start

    ok(
        "%d 行 × %d 列渲染 < %.2f s" % (PERF_ROWS, PERF_COLUMNS, PERF_SECONDS),
        elapsed < PERF_SECONDS,
        "耗时为 %.4f s" % elapsed,
        "耗时为 %.4f s（超过 %.2f s）" % (elapsed, PERF_SECONDS),
    )

    widths = set()
    for line in text.split("\n"):
        widths.add(width_of(line))
    ok(
        "整表每行显示宽度一致",
        len(widths) == 1,
        "所有行显示宽度相同",
        "出现 %d 种显示宽度：%r" % (len(widths), sorted(widths)[:6]),
    )


SCENARIOS = [
    ("width", "ascii", scenario_width_ascii),
    ("width", "east_asian", scenario_width_east_asian),
    ("width", "combining_emoji", scenario_width_combining_emoji),
    ("wrap", "ascii", scenario_wrap_ascii),
    ("wrap", "wide", scenario_wrap_wide),
    ("wrap", "combining", scenario_wrap_combining),
    ("align", "basic", scenario_align_basic),
    ("align", "center_residual", scenario_align_center_residual),
    ("edge", "shapes", scenario_edge_shapes),
    ("edge", "single_column", scenario_edge_single_column),
    ("perf", "large", scenario_perf_large),
]


def run_one(group, name, func):
    """跑一个场景，返回 (ok, expected, actual)。"""
    try:
        func()
    except Mismatch as exc:
        return False, exc.expected, exc.actual
    except Exception as exc:  # noqa: BLE001 - 直接把异常当作失败证据
        return False, "场景正常完成", "%s: %s" % (type(exc).__name__, exc)
    return True, "", ""


def child_main(key):
    for group, name, func in SCENARIOS:
        if "%s/%s" % (group, name) == key:
            passed, expected, actual = run_one(group, name, func)
            if passed:
                sys.stdout.write("PASS %s\n" % key)
                return 0
            sys.stdout.write("FAIL %s  期望=%s 实际=%s\n" % (key, brief(expected), brief(actual)))
            return 1
    sys.stdout.write("FAIL %s  期望=场景存在 实际=未知场景\n" % key)
    return 1


def run_with_watchdog(key):
    """在独立子进程里跑一个场景，超时或崩溃也算一次失败。"""
    timeout = PERF_TIMEOUT if key.startswith("perf/") else SCENARIO_TIMEOUT
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    try:
        proc = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "--_run-one", key],
            cwd=HERE,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "FAIL %s  期望=%.0f 秒内完成 实际=超时（看门狗 %.0f s）" % (key, timeout, timeout)
    text = proc.stdout.decode("utf-8", "replace")
    for line in reversed(text.splitlines()):
        if line.startswith("PASS ") or line.startswith("FAIL "):
            return line
    tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()
    detail = tail[-1] if tail else "无输出"
    return "FAIL %s  期望=场景正常完成 实际=子进程异常退出 exit=%s | %s" % (key, proc.returncode, brief(detail))


def main(argv):
    if "-list" in argv or "--list" in argv:
        for group, name, _ in SCENARIOS:
            print("%s/%s" % (group, name))
        return 0

    only = None
    if "--only" in argv:
        index = argv.index("--only")
        if index + 1 >= len(argv):
            print("--only 需要一个组名（width / wrap / align / edge / perf）")
            return 2
        only = argv[index + 1]

    selected = [(g, n) for g, n, _ in SCENARIOS if only is None or g == only]
    if not selected:
        print("没有匹配的场景组：%r" % (only,))
        return 2

    passed = 0
    for group, name in selected:
        line = run_with_watchdog("%s/%s" % (group, name))
        print(line)
        if line.startswith("PASS "):
            passed += 1
    print("结果：通过 %d/%d" % (passed, len(selected)))
    return 0 if passed == len(selected) else 1


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == "--_run-one":
        sys.exit(child_main(args[1]))
    sys.exit(main(args))
