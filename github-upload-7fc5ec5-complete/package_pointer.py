"""Resolve an explicit RFC 6901 selector inside a local JSON content package."""

import re


def resolve_json_pointer(document: object, pointer: str, label: str = "content package") -> object:
    if not isinstance(pointer, str) or (pointer and not pointer.startswith("/")):
        raise ValueError(f"{label} JSON Pointer must be empty or begin with '/'.")
    current = document
    if pointer == "":
        return current
    for raw_token in pointer[1:].split("/"):
        if re.search(r"~(?![01])", raw_token):
            raise ValueError(f"{label} JSON Pointer has an invalid escape sequence.")
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if token not in current:
                raise ValueError(f"{label} JSON Pointer does not resolve at {token!r}.")
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                raise ValueError(f"{label} JSON Pointer has an invalid array index {token!r}.")
            index = int(token)
            if index >= len(current):
                raise ValueError(f"{label} JSON Pointer array index {index} is out of range.")
            current = current[index]
        else:
            raise ValueError(f"{label} JSON Pointer traverses a scalar value.")
    return current
