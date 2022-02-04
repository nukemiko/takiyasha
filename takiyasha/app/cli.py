import shutil
import sys
from pathlib import Path
from time import time
from typing import Generator, IO

import click

from ..__version__ import version
from ..algorithms import (
    Decoder,
    NCMFormatDecoder,
    new_decoder
)
from ..algorithms.ncm import NCM_RC4Cipher
from ..exceptions import (
    CipherException,
    DecryptionException,
    UnsupportedDecryptionFormat
)
from ..metadata import new_tag
from ..metadata.common import TagWrapper
from ..utils import (
    get_audio_format,
    SUPPORTED_FORMATS_PATTERNS
)

# Parameters for click.core.Context()
_CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help'],
}
if 80 < shutil.get_terminal_size().columns < 120:
    _CONTEXT_SETTINGS['max_content_width'] = shutil.get_terminal_size().columns
elif 120 <= shutil.get_terminal_size().columns:
    _CONTEXT_SETTINGS['max_content_width'] = 120

# Metavars for all options and arguments
_METAVARS = {
    'paths_to_input': '</PATH/TO/FILES>...',
    'path_to_output': '[/DIR/OR/FILE]'
}
_HELP_CONTENTS = {
    'path_to_output': """Path to output file or dir.""",
    'write_to_stdout': """\b
    Output the contents of the unlocked file to the screen.
    It will occupy the STDOUT, and skip the metadata embedding.""",
    'without_metadata': """Do not embed found metadata in the output file.""",
    'show_supported_formats': """Show supported formats and exit.""",
    'show_version': """Show the version information and exit."""
}


def preprocess_input_paths(
        ctx: click.core.Context,
        param: click.core.Parameter,
        input_paths: tuple[Path]
):
    bool(ctx)
    bool(param)
    if len(input_paths) == 0:
        click.echo(ctx.get_usage(), err=True)
        click.echo(f"Try '{ctx.info_name} {ctx.help_option_names[0]}' for help.\n", err=True)
        raise click.ClickException(
            "Missing argument '{paths_to_input}'.".format_map(_METAVARS)
        )

    def filter_dirs():
        for path in input_paths:
            if path.is_dir():
                click.echo(
                    f"Warning: Skipped input directory '{path}'.",
                    err=True
                )
                continue
            yield path

    ret = tuple(filter_dirs())
    ctx.meta['input_paths'] = ret
    return ret


def show_supported_formats(
        ctx: click.core.Context,
        param: click.core.Parameter,
        value: str
):
    bool(param)
    if not value or ctx.resilient_parsing:
        return

    click.echo(
        'Supported encryption formats:\n'
        '(displayed using Unix shell-style wildcard format)\n\n'
        'The meaning of wildcard characters:\n'
        '    * - Match any character\n'
        '    ? - Match any single character\n', err=True
        )
    for encryption, patterns in SUPPORTED_FORMATS_PATTERNS.items():
        click.echo(f'{encryption.upper()} files: ', nl=False, err=True)
        patterns_map: list[list[str]] = []
        map_line: list[str] = []
        for idx, pattern in enumerate(patterns):
            map_line.append(pattern)
            if (idx + 1) % 4 == 0:
                patterns_map.append(map_line[:])
                map_line.clear()
        else:
            patterns_map.append(map_line[:])
            map_line.clear()
        for idx, line in enumerate(patterns_map):
            prefix = '\t\t'
            if idx + 1 == 1:
                line_str: str = '\t' + ', '.join(line)
            else:
                line_str: str = prefix + ', '.join(line)
            click.echo(line_str, err=True)

    ctx.exit()


def show_version(
        ctx: click.core.Context,
        param: click.core.Parameter,
        value: str
):
    bool(param)
    if not value or ctx.resilient_parsing:
        return

    click.echo(f"""Takiyasha version: {version()}""", err=True)
    click.echo(f"""Python version: {sys.version}""", err=True)
    click.echo(
        f"""\nSupport the project: https://github.com/nukemiko/takiyasha""",
        err=True
    )

    sys.exit()


@click.command(context_settings=_CONTEXT_SETTINGS)
@click.argument(
    'paths_to_input',
    metavar=_METAVARS['paths_to_input'],
    nargs=-1,
    type=click.Path(exists=True, readable=True, path_type=Path),
    callback=preprocess_input_paths
)
@click.option(
    '-o', '--output-path', 'path_to_output',
    metavar=_METAVARS['path_to_output'],
    default=Path.cwd(),
    show_default=True,
    type=click.Path(writable=True, path_type=Path),
    help=_HELP_CONTENTS['path_to_output']
)
@click.option(
    '-w', '--without-metadata', 'without_metadata',
    is_flag=True,
    help=_HELP_CONTENTS['without_metadata']
)
@click.option(
    '--formats', '--supported-formats', 'show_supported_formats',
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=show_supported_formats,
    help=_HELP_CONTENTS['show_supported_formats']
)
@click.option(
    '-S', '--stdout', 'write_to_stdout',
    is_flag=True,
    help=_HELP_CONTENTS['write_to_stdout']
)
@click.option(
    '-V', '--version',
    is_flag=True,
    is_eager=True,
    callback=show_version,
    expose_value=False,
    help=_HELP_CONTENTS['show_version']
)
def main(**kwargs):
    """\b
    Takiyasha - an unlocker for DRM protected music files, written by python
    Support the project: https://github.com/nukemiko/takiyasha

    \b
    Examples:
        takiyasha file1.qmcflac file2.mflac ...
        python -m takiyasha file3.mgg1 file4.ncm"""
    input_paths: tuple[Path] = kwargs['paths_to_input']
    output_path: Path = kwargs['path_to_output']
    write_to_stdout: bool = kwargs['write_to_stdout']
    without_metadata: bool = kwargs['without_metadata']

    if len(input_paths) > 1 and write_to_stdout:
        raise click.ClickException(
            "Output the unlocked data to the screen only if the input path is a single file."
        )
    if write_to_stdout:
        tasks: list[tuple[Decoder, IO[bytes]]] = [generate_stdout_task(input_paths[0])]
        without_metadata = True
    else:
        check_output_path(output_path, input_paths)
        tasks: list[tuple[Decoder, IO[bytes]]] = list(generate_tasks(*input_paths, output_path=output_path))

    for decoder, file in tasks:
        input_file_name: str = Path(decoder.name).name
        output_file_path: str = '<stdout>' if write_to_stdout else file.name
        output_file_name: str = Path(output_file_path).name
        totalsize: int = decoder.seek(0, 2)
        blksize: int = decoder.iter_blocksize
        progress: Progress = Progress(totalsize, blksize)
        decoder.seek(0, 0)

        # 解锁文件
        sys.stderr.write(f'[{progress}] Unlocking: {input_file_name} -> {output_file_name}\t\r')
        last_update_time: float = time()
        for blk in decoder:
            file.write(blk)
            progress.update()
            if time() - last_update_time >= 1:
                sys.stderr.write(f'[{progress}] Unlocking: {input_file_name} -> {output_file_name}\t\r')
                last_update_time: float = time()
        else:
            # 写入元数据
            if not without_metadata:
                sys.stderr.write('Embedding metadata...\r')
                file.seek(0, 0)
                if isinstance(decoder, NCMFormatDecoder) and isinstance(decoder.cipher, NCM_RC4Cipher):
                    tag: TagWrapper = new_tag(file)
                    tag.title = decoder.music_title
                    tag.artist = decoder.music_artists
                    tag.album = decoder.music_album
                    tag.comment = decoder.music_identifier
                    tag.cover = decoder.music_cover_data
                    file.seek(0, 0)
                    tag.save(file)
                else:
                    sys.stderr.write(
                        'Warning: Skipped metadata embedding, '
                        'because no metadata found.\r'
                    )
            else:
                sys.stderr.write('Warning: Skipped metadata embedding')
                if write_to_stdout:
                    sys.stderr.write(', because the output is STDOUT.\r')
                else:
                    sys.stderr.write('.\r')
            decoder.close()
            file.close()
            click.echo(
                f"Unlock finished: {input_file_name} -> {output_file_path}",
                err=True
            )


def check_output_path(path_to_output: Path, paths_to_input: tuple[Path]) -> None:
    output_path_can_be_file: bool = False
    if len(paths_to_input) == 1 and paths_to_input[0].is_file():
        output_path_can_be_file: bool = True

    if not (path_to_output.is_dir() or output_path_can_be_file):
        raise click.ClickException(
            'The output path can be a file only if the input path is a single file.'
        )


def generate_stdout_task(input_path: Path) -> tuple[Decoder, IO[bytes]]:
    try:
        decoder: Decoder = new_decoder(input_path)
    except (CipherException, DecryptionException) as exc:
        if isinstance(exc, UnsupportedDecryptionFormat):
            raise click.ClickException(
                f"Cannot unlock input file '{input_path}': "
                f"Unrecognized encryption format.",
            )
        else:
            raise click.ClickException(
                f"Cannot unlock input file '{input_path}': "
                f"Failed to unlock the data."
            )

    decoder.seek(0, 0)

    return decoder, sys.stdout.buffer


def generate_tasks(
        *input_paths: Path,
        output_path: Path
) -> Generator[tuple[Decoder, IO[bytes]], None, None]:
    for input_path in input_paths:
        try:
            decoder: Decoder = new_decoder(input_path)
        except (CipherException, DecryptionException) as exc:
            if isinstance(exc, UnsupportedDecryptionFormat):
                click.echo(
                    f"Warning: Skipped input file '{input_path}': "
                    f"Unrecognized encryption format.",
                    err=True
                )
            else:
                click.echo(
                    f"Warning: Skipped input file '{input_path}': "
                    f"Failed to unlock the data.",
                    err=True
                )
            continue

        audio_format: str = get_audio_format(decoder.read(32))
        if output_path.is_dir():
            new_output_path: Path = output_path / f'{input_path.stem}.{audio_format}'
        else:
            new_output_path: Path = output_path

        decoder.seek(0, 0)

        yield decoder, open(new_output_path, 'w+b')


class Progress:
    def __init__(self, totalsize: int, blksize: int, blkcount: int = 0):
        self.totalsize: int = totalsize
        self.blksize: int = blksize
        self.blkcount: int = blkcount

    def update(self, updated_blk: int = 1):
        self.blkcount += updated_blk

    def __repr__(self):
        return f'<Progress {self} ({self.blksize * self.blkcount}/{self.totalsize})>'

    def __str__(self):
        done_size: int = self.blksize * self.blkcount
        if done_size >= self.totalsize:
            return '100%'
        else:
            return '{:.2f}%'.format((done_size / self.totalsize) * 100)
