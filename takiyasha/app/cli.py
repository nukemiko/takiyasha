import shutil
import sys
from pathlib import Path
from time import time
from typing import IO, Optional

import click

from ..__version__ import version
from ..algorithms import new_decoder
from ..algorithms.common import Decoder
from ..exceptions import DecryptionException
from ..utils import SUPPORTED_FORMATS_PATTERNS

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
    It will occupy the STDOUT.""",
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
                    f"WARNING: Skipped input directory '{path}'.",
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

    click.echo('Supported encryption formats:\n', err=True)
    for encryption, patterns in SUPPORTED_FORMATS_PATTERNS.items():
        click.echo(f'{encryption.title()} files: ', nl=False, err=True)
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
    '--formats', '--supported-formats',
    is_flag=True,
    is_eager=True,
    callback=show_supported_formats,
    expose_value=False,
)
@click.option(
    '-S', '--stdout', 'write_to_stdout',
    is_flag=True,
    show_default=True,
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
    Support the project: https://github.com/nukemiko/takiyasha"""
    input_paths: tuple[Path] = kwargs['paths_to_input']
    output_path: Path = kwargs['path_to_output']
    write_to_stdout: bool = kwargs['write_to_stdout']
    check_output_path(output_path, input_paths)

    if len(input_paths) > 1 and write_to_stdout:
        raise click.ClickException(
            "Output the unlocked data to the screen only if the input path is a single file."
        )

    for path in input_paths:
        output_file: Optional[IO[bytes]] = unlock_flow(path, output_path, write_to_stdout=write_to_stdout)
        if output_file:
            output_file.close()


def check_output_path(path_to_output: Path, paths_to_input: tuple[Path]) -> None:
    output_path_can_be_file: bool = False
    if len(paths_to_input) == 1 and paths_to_input[0].is_file():
        output_path_can_be_file: bool = True

    if path_to_output.is_file() and not output_path_can_be_file:
        raise click.ClickException(
            'The output path can be a file only if the input path is a single file.'
        )


def unlock_percent(done: int, total: int):
    if done >= total:
        return '100%'
    else:
        return '{:.2f}%'.format((done / total) * 100)


def unlock_flow(
        input_path: Path,
        output_path: Path,
        write_to_stdout: bool = False
) -> Optional[IO[bytes]]:
    try:
        decoder: Decoder = new_decoder(input_path)
    except DecryptionException as exc:
        click.echo(f"WARNING: Skipped input file '{input_path.name}': {exc}", err=True)
        return
    audio_length: int = decoder.seek(0, 2)
    decoder.seek(0, 0)

    if write_to_stdout:
        output_file: IO[bytes] = sys.stdout.buffer
    else:
        if output_path.is_dir():
            audio_format: str = decoder.audio_format
            if not audio_format:
                audio_format: str = 'unlocked'
            new_output_path: Path = output_path / f'{input_path.stem}.{audio_format}'
        else:
            new_output_path: Path = output_path
        try:
            output_file: IO[bytes] = open(
                new_output_path, 'x+b'
            )
        except FileExistsError:
            click.echo(
                f"WARNING: Skipped input file '{input_path.name}': "
                f"Output path '{new_output_path}' already exists.",
                err=True
            )
            return

    writed_bytes: int = 0
    last_marked_time: float = time()
    click.echo(
        f"[{unlock_percent(writed_bytes, audio_length)}] "
        f"Unlocking: '{input_path.name}'\r",
        nl=False,
        err=True
    )
    for bytestringline in decoder:
        line_length: int = len(bytestringline)
        output_file.write(bytestringline)
        writed_bytes += line_length

        current_time: float = time()
        if current_time - last_marked_time >= 1:
            click.echo(
                f"[{unlock_percent(writed_bytes, audio_length)}] "
                f"Unlocking: '{input_path.name}'\r",
                nl=False,
                err=True
            )
            last_marked_time: float = current_time
    else:
        click.echo(
            f"Done: '{input_path.name}' -> '{Path(output_file.name).name}'",
            err=True
        )
        return output_file
