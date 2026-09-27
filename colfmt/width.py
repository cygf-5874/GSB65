"""列宽的度量：按终端显示宽度（East Asian Width + 组合记号）。"""

import unicodedata


def char_width(ch):
    """单个字符占用的列数。

    East Asian Width 为 W/F 的码点占 2 列；Unicode 类别为 Mn/Me 的组合记号
    占 0 列；其余（含 Ambiguous / Neutral）占 1 列。
    """
    if ord(ch) < 0x80:
        return 1
    if unicodedata.category(ch) in ("Mn", "Me"):
        return 0
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 2
    return 1


def display_width(text):
    """字符串占用的列数。"""
    total = 0
    for ch in text:
        if ord(ch) < 0x80:
            total += 1
        elif unicodedata.category(ch) in ("Mn", "Me"):
            continue
        elif unicodedata.east_asian_width(ch) in ("W", "F"):
            total += 2
        else:
            total += 1
    return total
