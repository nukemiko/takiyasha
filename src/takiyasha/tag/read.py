from __future__ import annotations

import re
from base64 import b64decode
from typing import IO

from mutagen import File as MutagenOpenFile, flac, id3, mp3, oggvorbis

REMOVABLE_PATTERNS = [
    re.compile(' ?- ?[Ss][Ii][Nn][Gg][Ll][Ee]$')
]


def read_values(fileobj: IO[bytes]) -> tuple[dict[str, list[str]], bytes | None]:
    fileobj.seek(0, 0)
    tag = MutagenOpenFile(fileobj)

    if isinstance(tag, (flac.FLAC, oggvorbis.OggVorbis)):
        kws: dict[str, list[str]] = {
            'title': tag.get('title'),
            'artists': tag.get('artist'),
            'album': tag.get('album'),
            'date': tag.get('date'),
            'label': tag.get('label'),
            'genre': tag.get('genre'),
            'description': tag.get('description'),
        }
    elif isinstance(tag, mp3.MP3):
        kws: dict[str, list[str]] = {}
        for kws_k, tag_k_seg in [('title', 'TIT2'), ('artists', 'TPE1'), ('album', 'TALB'),
                                 ('date', 'TDRC'), ('label', 'TXXX::LABEL'), ('genre', 'TCON'),
                                 ('description', 'COMM::')]:
            for _ in tag.keys():
                if _.startswith(tag_k_seg):
                    tag_k = _
                    break
            else:
                continue

            kws[kws_k] = list(tag[tag_k])
    else:
        return {}, None

    ret: dict[str, list[str]] = {k: v for k, v in kws.items() if v}

    title = ret.get('title')
    if title:
        new_title = ret['title'][:]
        for idx, i in enumerate(new_title):
            for pattern in REMOVABLE_PATTERNS:
                i = pattern.sub('', i)
            new_title[idx] = i
        ret['title'] = new_title

    return ret, extract_cover_data(tag)


def extract_cover_data(tag: flac.FLAC | mp3.MP3 | oggvorbis.OggVorbis) -> bytes | None:
    if isinstance(tag, flac.FLAC):
        for picture in tag.pictures:
            if getattr(picture, 'type', None) == 3:
                return getattr(picture, 'data', None)
    elif isinstance(tag, oggvorbis.OggVorbis):
        metadata_block_pictures: list[str] = tag.get('metadata_block_picture', [])
        for b64_mbp in metadata_block_pictures:
            try:
                mbp = b64decode(b64_mbp)
            except (TypeError, ValueError):
                continue
            try:
                picture = flac.Picture(mbp)
            except flac.error:
                continue
            if getattr(picture, 'type', None) == 3:
                return getattr(picture, 'data', None)
    elif isinstance(tag, mp3.MP3):
        for tag_k in tag:
            if tag_k.startswith('APIC'):
                apic: id3.APIC = tag[tag_k]
                break
        else:
            return

        return getattr(apic, 'data', None)
