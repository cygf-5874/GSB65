"""单元格文本的展开、折行与补白。"""

from .width import char_width, display_width

ALIGNMENTS = ("left", "right", "center")


def expand_tabs(text):
    """把 ``\\t`` 展开为空格。

    展开后相对文本起点（即单元格起点）的显示宽度前进到下一个 8 的倍数；
    起点宽度已经是 8 的倍数时补足 8 个空格。
    """
    if "\t" not in text:
        return text
    out = []
    column = 0
    for ch in text:
        if ch == "\t":
            spaces = 8 - column % 8
            out.append(" " * spaces)
            column += spaces
        else:
            out.append(ch)
            column += char_width(ch)
    return "".join(out)


def _units(text):
    """把文本切成「基字符 + 紧跟其后的组合记号」的不可分割单元。

    组合记号（显示宽度为 0 的码点，如 Mn/Me）附加到当前单元；出现在文本
    开头、没有基字符可依附的组合记号自己成为一个单元。
    """
    units = []
    for ch in text:
        if units and char_width(ch) == 0:
            units[-1] += ch
        else:
            units.append(ch)
    return units


def wrap_text(text, width):
    """把 ``text`` 按显示宽度 ``width`` 贪心折行，返回行的列表。

    一个不可分割单元要么整块留在当前行、要么整块挪到下一行；单个单元本身
    宽于 ``width`` 时它单独占一行（唯一允许超出列宽的情形）。
    ``text`` 为空或 ``width <= 0`` 时原样返回 ``[text]``。
    """
    if width <= 0 or text == "":
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
    """把一行按 ``align`` 补到 ``width`` 列（按显示宽度补空格）。"""
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
