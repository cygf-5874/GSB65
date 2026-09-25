"""colfmt —— 宽字符（CJK / 组合记号）表格渲染。

对外只暴露三件事：

* ``display_width(text)`` —— 字符串的显示宽度；
* ``wrap_text(text, width)`` —— 按显示宽度折行；
* ``render_table(...)`` —— 渲染整张表。

语义见 README「对外契约」一节。
"""

from .layout import ALIGNMENTS, pad_line, wrap_text
from .render import STYLES, render_table
from .width import char_width, display_width

__all__ = [
    "ALIGNMENTS",
    "STYLES",
    "char_width",
    "display_width",
    "pad_line",
    "render_table",
    "wrap_text",
]
__version__ = "0.3.0"
