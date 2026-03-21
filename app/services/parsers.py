def split_command_payload(text: str) -> str:
    parts = text.split(maxsplit=1)
    if len(parts) == 1:
        return ""
    return parts[1].strip()


def split_pipe_payload(payload: str, expected_parts: int) -> list[str]:
    parts = [part.strip() for part in payload.split("|")]
    if len(parts) != expected_parts:
        raise ValueError("invalid_payload")
    return parts


def parse_sizes_map(payload: str) -> dict[str, float]:
    result: dict[str, float] = {}
    chunks = [chunk.strip() for chunk in payload.split(",") if chunk.strip()]
    if not chunks:
        raise ValueError("invalid_sizes")
    for chunk in chunks:
        if ":" not in chunk:
            raise ValueError("invalid_sizes")
        size, price = [x.strip() for x in chunk.split(":", maxsplit=1)]
        if not size:
            raise ValueError("invalid_sizes")
        result[size.upper()] = float(price)
    return result
