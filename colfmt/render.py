"""表格渲染：把二维文本渲染成带边框的等宽表格。"""

from .layout import ALIGNMENTS, expand_tabs, pad_line, wrap_text
from .width import display_width

# 每种边框风格用到的字形：``h`` 横线、``v`` 竖线，三组分别是顶行 / 中间分隔行 /
# 底行的「左端 / 交叉 / 右端」。
STYLES = {
    "ascii": {
        "h": "-",
        "v": "|",
        "top": ("+", "+", "+"),
        "mid": ("+", "+", "+"),
        "bottom": ("+", "+", "+"),
    },
    "light": {
        "h": "\u2500",
        "v": "\u2502",
        "top": ("\u250c", "\u252c", "\u2510"),
        "mid": ("\u251c", "\u253c", "\u2524"),
        "bottom": ("\u2514", "\u2534", "\u2518"),
    },
}


def _resolve_align(align, columns):
    aligns = [align] * columns if isinstance(align, str) else list(align)
    if len(aligns) != columns:
        raise ValueError("align 长度与列数不符：%d != %d" % (len(aligns), columns))
    for item in aligns:
        if item not in ALIGNMENTS:
            raise ValueError("unknown align: %r" % (item,))
    return aligns


def _resolve_widths(widths, columns):
    if widths is None:
        return None
    widths = list(widths)
    if len(widths) != columns:
        raise ValueError("widths 长度与列数不符：%d != %d" % (len(widths), columns))
    return widths


def _process_cell(text):
    """单元格原始文本 -> 参与宽度计算与折行的文本。

    顺序固定：① ``|`` -> ``\\|``；② ``\\n`` -> ``<br>``；③ ``\\t`` 展开。
    """
    return expand_tabs(text.replace("|", "\\|").replace("\n", "<br>"))


def _auto_widths(rows, headers, columns):
    result = []
    for j in range(columns):
        best = 0
        if headers is not None:
            best = max(best, display_width(headers[j]))
        for row in rows:
            best = max(best, display_width(row[j]))
        result.append(best)
    return result


def _block(cells, widths, aligns):
    """把一行单元格渲染成若干物理行；每行是各列已补白的片段列表。"""
    wrapped = [wrap_text(cells[j], widths[j]) for j in range(len(widths))]
    height = max(len(item) for item in wrapped)
    block = []
    for i in range(height):
        parts = []
        for j, width in enumerate(widths):
            line = wrapped[j][i] if i < len(wrapped[j]) else ""
            parts.append(pad_line(line, width, aligns[j]))
        block.append(parts)
    return block


def _rule(style, widths, kind):
    left, middle, right = STYLES[style][kind]
    horizontal = STYLES[style]["h"]
    # 每个单元格在内容两侧各有一个空格，所以横线段长是列宽 + 2。
    return left + middle.join(horizontal * (w + 2) for w in widths) + right


def render_table(rows, headers=None, widths=None, align="left", style="ascii"):
    """把 ``rows``（可选 ``headers``）渲染成文本表格。

    语义见 README「对外契约」一节。``widths`` 为 ``None`` 时按内容取每列最大显示宽度。
    """
    if style not in ("ascii", "light", "none"):
        raise ValueError("unknown style: %r" % (style,))

    if headers is not None:
        columns = len(headers)
    elif rows:
        columns = len(rows[0])
    else:
        columns = 0
    if columns == 0:
        return ""

    grid = [[_process_cell(cell) for cell in row] for row in rows]
    head = [_process_cell(cell) for cell in headers] if headers is not None else None
    for row in grid:
        if len(row) != columns:
            raise ValueError("每行的列数必须一致")

    resolved = _resolve_widths(widths, columns)
    if resolved is None:
        resolved = _auto_widths(grid, head, columns)
    aligns = _resolve_align(align, columns)

    if style == "none":
        physical = []
        if head is not None:
            physical.extend(" ".join(parts).rstrip() for parts in _block(head, resolved, aligns))
        for row in grid:
            physical.extend(" ".join(parts).rstrip() for parts in _block(row, resolved, aligns))
        return "\n".join(physical)

    vertical = STYLES[style]["v"]
    lines = [_rule(style, resolved, "top")]
    if head is not None:
        for parts in _block(head, resolved, aligns):
            lines.append(vertical + vertical.join(" " + p + " " for p in parts) + vertical)
        if grid:
            lines.append(_rule(style, resolved, "mid"))
    for index, row in enumerate(grid):
        for parts in _block(row, resolved, aligns):
            lines.append(vertical + vertical.join(" " + p + " " for p in parts) + vertical)
        if index != len(grid) - 1:
            lines.append(_rule(style, resolved, "mid"))
    lines.append(_rule(style, resolved, "bottom"))
    return "\n".join(lines)
