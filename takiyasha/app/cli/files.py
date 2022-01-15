import errno
import os
from typing import Generator, Optional, Union

import click

from ...typehints import PathType
from ...utils import get_encryption_format


def search_encrypted_files(
        *input_paths: Union[PathType],
        recursive: bool = False
) -> Generator[tuple[str, str], None, None]:
    for path in input_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
        
        if os.path.isfile(path):
            enctype: Optional[str] = get_encryption_format(path)
            if enctype:
                yield path, enctype
        elif os.path.isdir(path):
            if recursive:
                for root, dirs, files in os.walk(path):
                    dirpaths: list[str] = [os.path.join(root, _) for _ in dirs]
                    filepaths: list[str] = [os.path.join(root, _) for _ in files]
                    yield from search_encrypted_files(*filepaths, *dirpaths)
            else:
                click.echo(f"Skipped directory: '{path}'")
