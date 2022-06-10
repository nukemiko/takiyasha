from __future__ import annotations

from base64 import b64decode
from typing import IO

from mutagen import flac, id3, mp3, oggvorbis


def read_values(fileobj: IO[bytes]) -> tuple[dict[str, list[str]], bytes | None]:
    for tagtype in flac.FLAC, mp3.MP3, oggvorbis.OggVorbis:
        fileobj.seek(0, 0)
        try:
            tag = tagtype(fileobj)
            break
        except (flac.error, mp3.error, oggvorbis.error):
            pass
    else:
        return {}, None

    if isinstance(tag, (flac.FLAC, oggvorbis.OggVorbis)):
        kws = {
            'title': tag.get('title'),
            'artists': tag.get('artist'),
            'album': tag.get('album'),
            'date': tag.get('date'),
            'label': tag.get('label'),
            'genre': tag.get('genre'),
            'description': tag.get('description'),
        }
    elif isinstance(tag, mp3.MP3):
        kws = {}
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

    ret = {k: v for k, v in kws.items() if v}

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
