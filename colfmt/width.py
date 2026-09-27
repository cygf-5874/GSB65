"""列宽的度量。"""

import unicodedata
from functools import lru_cache

_WIDE = ("W", "F")
_ZERO = ("Mn", "Me")


@lru_cache(maxsize=None)
def char_width(ch):
    """单个字符占用的列数。

    East Asian Width 为 ``W``/``F`` 的记 2；Unicode 类别为 ``Mn``/``Me``
    的组合记号记 0；其余（含 ``A``/``N``）记 1。
    """
    if unicodedata.east_asian_width(ch) in _WIDE:
        return 2
    if unicodedata.category(ch) in _ZERO:
        return 0
    return 1


def display_width(text):
    """字符串占用的列数。"""
    total = 0
    for ch in text:
        total += char_width(ch)
    return total
