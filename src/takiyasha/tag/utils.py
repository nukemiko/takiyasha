from __future__ import annotations


def sniff_image_ext_mimetype(data: bytes) -> tuple[str, str] | None:
    if data.startswith(b'\xff\xd8\xff'):
        return 'jpg', 'image/jpeg'
    elif data.startswith(b'\x89PNG'):
        return 'png', 'image/png'
    elif data.startswith(b'BM'):
        return 'bmp', 'image/bmp'
