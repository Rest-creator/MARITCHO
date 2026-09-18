import re

_TAG_RE = re.compile(r"<[^>]*>")


def strip_tags(value: str) -> str:
    return _TAG_RE.sub("", value).strip()
