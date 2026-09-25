"""单元格文本的换行与补白。"""

from .width import display_width

ALIGNMENTS = ("left", "right", "center")


def wrap_text(text, width):
    """把 ``text`` 按显示宽度 ``width`` 折行，返回行的列表。"""
    return [text]


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
