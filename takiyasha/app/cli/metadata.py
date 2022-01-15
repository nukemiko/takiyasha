from typing import Callable, IO, Type

from ...metadata.common import TagProxy
from ...metadata.flac import Flac
from ...metadata.mp3 import Mp3
from ...metadata.ogg import Ogg


def embed_metadata_from_otherside(tag: TagProxy, metadata: dict[str, ...]):
    raise NotImplementedError


def embed_metadata_from_cloudmusic(tag: TagProxy, metadata: dict[str, ...]):
    # Keys of cloudmusic's metadata:
    # ['format',
    #  'musicId',
    #  'musicName',  str
    #  'artist',  list[list[str, int]]
    #  'album',  str
    #  'albumId',
    #  'albumPicDocId',
    #  'albumPic',
    #  'mvId',
    #  'flag',
    #  'bitrate',
    #  'duration',
    #  'alias',
    #  'transNames']
    tag.title = metadata['musicName']
    tag.artist = metadata['artist'][0][0]
    tag.album = metadata['album']
    tag.comment = metadata['identifier']
    tag.set_cover(metadata['cover_data'])
    
    tag.save()
    if tag.filething_seekable:
        tag.filething.close()


AUDIOFMT_TAGTYPE = {
    'flac': Flac,
    'mp3': Mp3,
    'ogg': Ogg
}
ENCRYPTION_EMBED_METHOD_MAP = {
    'NCM': embed_metadata_from_cloudmusic
}


def embed_metadata(fileobj: IO[bytes],
                   audiofmt: str,
                   metadata: dict[str, ...],
                   encryption: str = None
                   ):
    tag_class: Type[TagProxy] = AUDIOFMT_TAGTYPE.get(audiofmt)
    embed_method: Callable[[TagProxy, dict[str, ...]], None] = ENCRYPTION_EMBED_METHOD_MAP.get(encryption)
    
    if not metadata:
        fileobj.close()
        return
    if not tag_class:
        fileobj.close()
        return
    if not embed_method and encryption is not None:
        fileobj.close()
        return
    
    tag: TagProxy = tag_class(fileobj)
    embed_method(tag, metadata)
