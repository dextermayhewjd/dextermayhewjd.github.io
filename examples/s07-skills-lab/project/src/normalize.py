def normalize_first(items):
    """Contract: an empty input returns an empty string."""
    if not items:
        return ""
    return items[0].strip()
