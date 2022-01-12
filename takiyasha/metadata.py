from typing import IO, Union

from mutagen import File, FileType, flac, id3, mp3, ogg

from .typehints import PathType, PathType_tuple

__all__ = ['embed_metadata']


def _save_tag(filething: Union[PathType, IO[bytes]], tag: FileType):
    if isinstance(filething, PathType_tuple):
        tag.save(filething)
    else:
        filething.seek(0, 0)
        tag.save(filething)
        filething.seek(0, 0)


def _prepare_to_embed_cover_image(
        picture: Union[flac.Picture, id3.APIC],
        cover_data: bytes,
        content_type: int
):
    try:
        if cover_data.startswith(b'\x89PNG'):
            picture.mime = 'image/png'
        else:
            picture.mime = 'image/jpeg'
    except TypeError:
        return
    else:
        # picture.encoding = 0
        picture.type = content_type
        picture.data = cover_data


def embed_metadata(
        filething: Union[PathType, IO[bytes]],
        title: str = None,
        artist: str = None,
        album: str = None,
        comment: str = None,
        cover_data: bytes = None
):
    audiotag: Union[FileType, mp3.ID3FileType] = File(filething)
    if not isinstance(audiotag, (flac.FLAC, ogg.OggFileType, mp3.MP3)):
        raise NotImplementedError(f"'{type(audiotag).__name__}' is not supported")
    
    # embed cover image
    if cover_data is not None:
        if isinstance(audiotag, mp3.ID3FileType):  # for MP3 format
            cover: id3.APIC = id3.APIC()
            _prepare_to_embed_cover_image(cover, cover_data, 6)
            audiotag.tags.add(cover)
        else:  # for FLAC and OGG format
            cover: flac.Picture = flac.Picture()
            _prepare_to_embed_cover_image(cover, cover_data, 3)
            audiotag.clear_pictures()
            audiotag.add_picture(cover)
        _save_tag(filething, audiotag)
    
    # embed metadata
    if isinstance(audiotag, mp3.ID3FileType):
        easymp3tag = mp3.EasyMP3(filething)
        easymp3tag['title'] = 'placeholder'
        if comment is not None:
            easymp3tag.tags.RegisterTestKey('comment', 'COMM')
            easymp3tag['comment'] = comment
        easymp3tag['title'] = title
        easymp3tag['album'] = album
        easymp3tag['artist'] = artist
        _save_tag(filething, easymp3tag)
    else:
        if comment is not None:
            audiotag['description'] = comment
        audiotag['title'] = title
        audiotag['album'] = album
        audiotag['artist'] = artist
        _save_tag(filething, audiotag)
    
    return filething
