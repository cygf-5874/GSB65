"""列宽的度量。"""


def char_width(ch):
    """单个字符占用的列数。"""
    return 1


def display_width(text):
    """字符串占用的列数。"""
    total = 0
    for ch in text:
        total += char_width(ch)
    return total
