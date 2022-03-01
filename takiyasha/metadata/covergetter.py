from typing import Union
from urllib.parse import urlparse

import requests

from ..algorithms import NCMFormatDecoder


def reqget(*args, **kwargs) -> requests.Response:
    resp = requests.get(*args, **kwargs)
    resp.raise_for_status()
    return resp


class QQMusicCoverGetter:
    def __init__(self, pmid: str, type_: int = 1):
        self._cover_data: bytes = reqget(self._api_entrypoint + f'/music/qq-cover/{type_}/{pmid}').content

    @property
    def cover_data(self) -> bytes:
        return self._cover_data

    def __bytes__(self) -> bytes:
        return self._cover_data

    _api_entrypoint: str = 'https://um-api.ixarea.com'

    @classmethod
    def from_metadata(cls, title: str, artist: str = None, album: str = None):
        payload = {
            'Title': title,
            'Artist': artist,
            'Album': album
        }
        cover_type_id: dict[str, Union[str, int]] = reqget(cls._api_entrypoint + '/music/qq-cover', params=payload).json()
        cover_type: int = cover_type_id['Type']
        cover_pmid: str = cover_type_id['Id']

        return cls(cover_pmid, cover_type)

    @classmethod
    def from_music_id(cls, music_id: int):
        detail: dict = reqget(cls._api_entrypoint + f'/meta/qq-music-raw/{music_id}').json()
        pmid: str = detail['req_1']['data']['track_info']['album']['pmid']

        return cls(pmid)


class CloudMusicCoverGetter:
    def __init__(self, cover_url: str):
        if cover_url is None:
            self._cover_data: bytes = b''
        else:
            parse_result = urlparse(cover_url)
            if 'music.126.net' not in parse_result.netloc:
                raise ValueError('cover url is not from CloudMusic')
            self._cover_data: bytes = reqget(cover_url).content

    @property
    def cover_data(self) -> bytes:
        return self._cover_data

    def __bytes__(self) -> bytes:
        return self._cover_data

    @classmethod
    def from_decoder(cls, decoder: NCMFormatDecoder):
        return cls(decoder.metadata.get('albumPic'))
