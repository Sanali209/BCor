"""Утилиты форматирования данных для отображения в UI и логах."""
import math


def format_size(size_bytes: int) -> str:
    """Нормализует байты в читаемый формат (KB, MB, GB)."""
    if size_bytes == 0:
        return "0 B"

    units = ("B", "KB", "MB", "GB", "TB", "PB")
    i = 0
    size = float(size_bytes)
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1

    return f"{size:.1f} {units[i]}"


def format_number(num: int) -> str:
    """Форматирует большие числа с суффиксами (K, M, B)."""
    if num < 1000:
        return str(num)

    units = ("", "K", "M", "B")
    i = 0
    val = float(num)
    while val >= 1000.0 and i < len(units) - 1:
        val /= 1000.0
        i += 1

    return f"{val:.1f}{units[i]}"
