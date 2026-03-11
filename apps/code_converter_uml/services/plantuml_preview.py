import zlib
from typing import Optional

from django.conf import settings


PLANTUML_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"


def _encode_6bit(value: int) -> str:
    if value < 0:
        value = 0
    if value > 63:
        value = 63
    return PLANTUML_ALPHABET[value]


def _append_3_bytes(b1: int, b2: int, b3: int) -> str:
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return "".join(_encode_6bit(part) for part in (c1, c2, c3, c4))


def encode_plantuml(uml_text: str) -> str:
    compressed = zlib.compress(uml_text.encode("utf-8"))
    # PlantUML expects raw DEFLATE (no zlib header/footer).
    compressed = compressed[2:-4]

    encoded = []
    for index in range(0, len(compressed), 3):
        chunk = compressed[index : index + 3]
        if len(chunk) == 3:
            encoded.append(_append_3_bytes(chunk[0], chunk[1], chunk[2]))
        elif len(chunk) == 2:
            encoded.append(_append_3_bytes(chunk[0], chunk[1], 0))
        else:
            encoded.append(_append_3_bytes(chunk[0], 0, 0))
    return "".join(encoded)


def build_plantuml_preview_url(uml_text: str, endpoint: Optional[str] = None) -> str:
    base_url = endpoint or getattr(
        settings,
        "PLANTUML_SERVER_URL",
        "https://www.plantuml.com/plantuml/svg",
    )
    encoded = encode_plantuml(uml_text)
    return f"{base_url.rstrip('/')}/{encoded}"
