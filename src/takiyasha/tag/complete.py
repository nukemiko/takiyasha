from __future__ import annotations

from typing import IO

from . import read, retrieve_convert, write
from ..utils import warn


def complete_from_cloudmusic(destfile: IO[bytes],
                             ncm_tagdata: dict,
                             cover_data: bytes | None = None,
                             search_tag: bool = False
                             ) -> bool:
    return_status = True

    tag_data = retrieve_convert.convert_ncm_tag(ncm_tagdata)
    cover_url: str | None = ncm_tagdata.get('albumPic')

    if search_tag:
        try:
            song_result = retrieve_convert.find_song_result(
                'cloudmusic', tag_data['title'], tag_data['artists']
            )
        except Exception as exc:
            warn(f"获取 '{destfile.name}' 的标签信息时出错："
                 f"{type(exc).__name__}: {exc}"
                 )
            return_status = False
        else:
            if song_result:
                tag_data.update(retrieve_convert.convert_song_result(song_result))

        if not cover_data and cover_url:
            try:
                cover_data = retrieve_convert.retrieve_cover_data(cover_url)
            except Exception as exc:
                warn(f"获取 '{destfile.name}' 的封面信息时出错："
                     f"{type(exc).__name__}: {exc}"
                     )
                return_status = False

    destfile.seek(0, 0)
    write.write_values(destfile, **tag_data, cover_data=cover_data)

    return return_status


def complete_from_qqmusic(destfile: IO[bytes], search_tag: bool = False) -> bool:
    return_status = True

    destfile.seek(0, 0)
    tag_data, cover_data = read.read_values(destfile)
    title: list[str] | None = tag_data.get('title')
    artists: list[str] | None = tag_data.get('artists')

    if search_tag and title and artists:
        try:
            song_result = retrieve_convert.find_song_result('qqmusic', title, artists)
        except Exception as exc:
            warn(f"获取 '{destfile.name}' 的标签信息时出错："
                 f"{type(exc).__name__}: {exc}"
                 )
            cover_url: str | None = None
            return_status = False
        else:
            if song_result:
                tag_data.update(retrieve_convert.convert_song_result(song_result))
                cover_url: str | None = song_result.coverurl
            else:
                cover_url: str | None = None

        if not cover_data and cover_url:
            try:
                cover_data = retrieve_convert.retrieve_cover_data(cover_url)
            except Exception as exc:
                warn(f"获取 '{destfile.name}' 的封面信息时出错："
                     f"{type(exc).__name__}: {exc}"
                     )
                return_status = False

        destfile.seek(0, 0)
        write.write_values(destfile, **tag_data, cover_data=cover_data)

        return return_status
