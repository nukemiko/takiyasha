from __future__ import annotations

from typing import Literal, Union

import requests
from tagfindutils import cloudmusic, qqmusic
from tagfindutils.cloudmusic import CloudMusicSearchResult
from tagfindutils.qqmusic import QQMusicSearchResult

SupportsSearchResult = Union[cloudmusic.CloudMusicSearchResult, qqmusic.QQMusicSearchResult]
SupportsSongDetail = Union[cloudmusic.CloudMusicSongDetail, qqmusic.QQMusicSongDetail]


def find_song_result(source: Literal['cloudmusic', 'qqmusic'],
                     title: list[str],
                     artists: list[str] | None = None,
                     ) -> SupportsSongDetail | SupportsSearchResult | None:
    if artists is None:
        artists = []

    keywords = title[:]
    if artists:
        keywords.extend(artists)

    if source == 'cloudmusic':
        searcher = cloudmusic.search
    elif source == 'qqmusic':
        searcher = qqmusic.search
    else:
        raise ValueError(f"tag search source '{source}' is not supported")

    search_results: list[CloudMusicSearchResult] | list[QQMusicSearchResult] = searcher(*keywords)
    if not len(search_results):
        return None
    else:
        most_relevant: SupportsSongDetail | SupportsSearchResult | None = search_results[0].get_detail()
        if not most_relevant:
            most_relevant: SupportsSongDetail | SupportsSearchResult | None = search_results[0]

    return most_relevant


def retrieve_cover_data(url: str) -> bytes:
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.content


def convert_song_result(song_result: SupportsSongDetail | SupportsSearchResult
                        ) -> dict[str, list[str]]:
    kws = {}
    if song_result.songname:
        kws['title'] = [song_result.songname]
    if song_result.artists:
        kws['artists'] = song_result.artists
    if song_result.album:
        kws['album'] = [song_result.album]
    if song_result.publish_time:
        kws['date'] = [str(song_result.publish_time.year)]
    if getattr(song_result, 'genre', None):
        kws['genre'] = getattr(song_result, 'genre')
    if getattr(song_result, 'company', None):
        kws['label'] = getattr(song_result, 'company')

    return kws


def convert_ncm_tag(ncm_tagdata: dict) -> dict[str, list[str]]:
    ret = {
        'title': [ncm_tagdata['musicName']],
        'artists': [_[0] for _ in ncm_tagdata['artist']],
        'album': [ncm_tagdata['album']]
    }
    desc = ncm_tagdata.get('identifier')
    if desc:
        ret['description'] = desc

    return ret  # type: ignore
