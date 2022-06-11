from __future__ import annotations

from base64 import b64decode, b64encode
from functools import partial
from typing import IO

from mutagen import File as MutagenOpenFile, flac, id3, mp3, oggvorbis

from .utils import sniff_image_ext_mimetype


def write_values(fileobj: IO[bytes],
                 title: list[str] | None = None,
                 artists: list[str] | None = None,
                 album: list[str] | None = None,
                 date: list[str] | None = None,
                 label: list[str] | None = None,
                 genre: list[str] | None = None,
                 description: list[str] | None = None,
                 cover_data: bytes | None = None
                 ) -> None:
    fileobj.seek(0, 0)
    tag = MutagenOpenFile(fileobj)

    kws = {
        'title': title,
        'artists': artists,
        'album': album,
        'date': date,
        'label': label,
        'genre': genre,
        'description': description
    }
    kws = {k: v for k, v in kws.items() if v}

    if isinstance(tag, (flac.FLAC, oggvorbis.OggVorbis)):
        for k, v in kws.items():
            if k == 'artists':
                tag['artist'] = v
            else:
                tag[k] = v
    elif isinstance(tag, mp3.MP3):
        for kws_k, tag_k_seg, tag_v_cls in [
            ('title', 'TIT2', id3.TIT2), ('artists', 'TPE1', id3.TPE1),
            ('album', 'TALB', id3.TALB), ('date', 'TDRC', id3.TDRC),
            ('label', 'TXXX::LABEL', partial(id3.TXXX, desc='LABEL')),
            ('genre', 'TCON', id3.TCON)
        ]:
            for _ in tag.keys():
                if _.startswith(tag_k_seg):
                    tag_k = _
                    break
            else:
                continue

            if kws_k in kws:
                tag[tag_k] = tag_v_cls(text=kws[kws_k])

        desc = kws.get('description')
        if desc:
            orig_tag_kws = {k: v for k, v in tag.items() if not k.startswith('COMM::')}
            tag.clear()
            orig_tag_kws['COMM::XXX'] = id3.COMM(lang='XXX', text=desc)
            tag.update(orig_tag_kws)
    else:
        return

    if cover_data:
        set_cover_data(tag, cover_data)

    fileobj.seek(0, 0)
    tag.save(fileobj)


def set_cover_data(tag: flac.FLAC | mp3.MP3 | oggvorbis.OggVorbis,
                   cover_data: bytes
                   ) -> None:
    ext_mimetype = sniff_image_ext_mimetype(cover_data)
    if ext_mimetype:
        ext, mime = ext_mimetype
    else:
        ext, mime = '', 'application/octet-stream'

    if isinstance(tag, flac.FLAC):
        new_pictures: list[flac.Picture] = [_ for _ in tag.pictures if getattr(_, 'type', None) != 3]
        cover_picture = flac.Picture()
        cover_picture.type = 3
        cover_picture.data = cover_data
        cover_picture.mime = mime
        new_pictures.insert(0, cover_picture)

        tag.clear_pictures()
        for picture in new_pictures:
            tag.add_picture(picture)
    elif isinstance(tag, oggvorbis.OggVorbis):
        metadata_block_pictures: list[str] = tag.get('metadata_block_picture', [])[:]

        new_pictures: list[flac.Picture] = []
        for b64_mbp in metadata_block_pictures:
            try:
                mbp = b64decode(b64_mbp)
            except (TypeError, ValueError):
                continue
            try:
                picture = flac.Picture(mbp)
            except flac.error:
                continue
            if getattr(picture, 'type', None) != 3:
                new_pictures.append(picture)

        cover_picture = flac.Picture()
        cover_picture.type = 3
        cover_picture.data = cover_data
        cover_picture.mime = mime
        cover_mbp = cover_picture.write()
        b64_cover_mbp = b64encode(cover_mbp).decode('ascii')

        metadata_block_pictures.insert(0, b64_cover_mbp)

        tag['metadata_block_picture'] = metadata_block_pictures
    elif isinstance(tag, mp3.MP3):
        apic = id3.APIC(data=cover_data, type=3, mime=mime)
        orig_tag_kws = {k: v for k, v in tag.items() if not k.startswith('APIC:')}
        tag.clear()
        orig_tag_kws['APIC:'] = apic
        tag.update(orig_tag_kws)
