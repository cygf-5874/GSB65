"""单元格文本的换行与补白。"""

import unicodedata

from .width import display_width

ALIGNMENTS = ("left", "right", "center")


def _units(text):
    """把文本切成「基字符 + 紧跟其后的组合记号」这样的不可分割单元。"""
    units = []
    for ch in text:
        if units and unicodedata.category(ch) in ("Mn", "Me"):
            units[-1] += ch
        else:
            units.append(ch)
    return units


def wrap_text(text, width):
    """把 ``text`` 按显示宽度 ``width`` 贪心折行，返回行的列表。

    一个单元要么整块留在当前行、要么整块挪到下一行；单个单元的显示宽度
    本身就大于 ``width`` 时，它单独占一行（唯一允许超出列宽的情形）。
    ``text`` 为空或 ``width <= 0`` 时返回 ``[text]``。
    """
    if not text or width <= 0:
        return [text]
    lines = []
    current = ""
    current_width = 0
    for unit in _units(text):
        unit_width = display_width(unit)
        if current and current_width + unit_width > width:
            lines.append(current)
            current = unit
            current_width = unit_width
        else:
            current += unit
            current_width += unit_width
    lines.append(current)
    return lines


def pad_line(line, width, align):
    """把一行按 ``align`` 补到 ``width`` 列。"""
    if align not in ALIGNMENTS:
        raise ValueError("unknown align: %r" % (align,))
    gap = width - display_width(line)
    if gap <= 0:
        return line
    if align == "right":
        return " " * gap + line
    if align == "center":
        left = gap // 2
        return " " * left + line + " " * (gap - left)
    return line + " " * gap
