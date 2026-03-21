def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string (KB, MB, GB)."""
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
    """Format large numbers with suffixes (K, M, B)."""
    if num < 1000:
        return str(num)

    units = ("", "K", "M", "B")
    i = 0
    val = float(num)
    while val >= 1000.0 and i < len(units) - 1:
        val /= 1000.0
        i += 1

    return f"{val:.1f}{units[i]}"
