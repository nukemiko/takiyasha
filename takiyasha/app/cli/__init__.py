import os
import sys
from typing import Generator

import click

from .files import search_encrypted_files
from .metadata import embed_metadata
from .unlock import unlock
from ...__version__ import version
from ...exceptions import CLIError
from ...utils import SUPPORTED_FORMATS_PATTERNS

CONTEXT_SETTINGS = {
    'help_option_names': ['-h', '--help']
}


def _print_supported_enctypes(ctx: click.core.Context,
                              param: click.core.Option,
                              value: bool
                              ):
    if param:
        pass
    if not value or ctx.resilient_parsing:
        return
    
    click.echo('Supported encryption formats:\n')
    for enctype, patterns in SUPPORTED_FORMATS_PATTERNS.items():
        click.echo(f'{enctype} files: ', nl=False)
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
            click.echo(line_str)
        click.echo()
    
    ctx.exit()


def _print_version_info(ctx: click.core.Context,
                        param: click.core.Option,
                        value: bool
                        ):
    if param:
        pass
    if not value or ctx.resilient_parsing:
        return
    
    click.echo(f"""Takiyasha version: {version()}""")
    click.echo(f"""Python version: {sys.version}""")
    click.echo(f"""Support the project: https://github.com/nukemiko/takiyasha""")
    
    ctx.exit()


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    '-o', '--output', 'output_path',
    metavar='PATH', show_default=True, default=os.getcwd(),
    type=click.Path(writable=True),
    help="""\b
    Path to output file or dir."""
)
@click.option(
    '-r', '--recursive', 'recursively',
    is_flag=True, show_default=True,
    help="""\b
    Also unlock supported files in subdirectories
    during unlocking."""
)
@click.option(
    '-n', '--without-metadata',
    is_flag=True, show_default=True, default=False,
    help="""\b
    Do not embed metadata found in the source file
    into the unlocked file."""
)
@click.option(
    '-q', '--quiet', 'donot_print_ok',
    is_flag=True, show_default=True,
    help="""\b
    Don't print OK for each unlocked file."""
)
@click.option(
    '--exts', '--supported-exts',
    is_flag=True, is_eager=True, callback=_print_supported_enctypes,
    help="""\b
    Show supported file extensions and exit."""
)
@click.option(
    '-V', '--version',
    is_flag=True, is_eager=True, callback=_print_version_info,
    help="""\b
    Show the version information and exit."""
)
# @click.option(
#     '--test',
#     is_flag=True, is_eager=True, callback=_inspect_params
# )
@click.argument(
    'paths_to_input',
    metavar='[/PATH/TO/INPUT]...', nargs=-1,
    type=click.Path(exists=True, readable=True)
)
def main(**params):
    """\b
    Takiyasha - DRM protected music file unlocker, written by python
    Support the project: https://github.com/nukemiko/takiyasha"""
    input_paths: tuple[str] = params['paths_to_input']
    output_path: str = params['output_path']
    recursively: bool = params['recursively']
    without_metadata: bool = params['without_metadata']
    donot_print_ok: bool = params['donot_print_ok']
    
    if len(input_paths) == 0:
        click.echo(
            "Error: No file or directory specified. Nothing works to do.\n"
            "Use the '-h/--help' option to get more help information.",
            err=True
        )
        exit(1)
    elif len(input_paths) != 1:
        if not os.path.exists(output_path):
            click.echo(
                "Error: More than 1 input path was given, but the output path is not exist.",
                err=True
            )
            exit(1)
        if not os.path.isdir(output_path):
            click.echo(
                "Error: More than 1 input path was given, but the output path is not a directory.",
                err=True
            )
            exit(1)
    elif len(input_paths) == 1:
        if os.path.isdir(input_paths[0]):
            if not os.path.exists(output_path):
                click.echo(
                    "Error: A directory path was gaven, but the output path is not exist.",
                    err=True
                )
                exit(1)
            if not os.path.isdir(output_path):
                click.echo(
                    "Error: A directory path was gaven, but the output is not a directory.",
                    err=True
                )
                exit(1)
    if not donot_print_ok:
        if recursively:
            click.echo(
                "The '-r/--recursive' option is specified, "
                "will search and unlock specified paths and all its subdirectories for supported files."
            )
        else:
            click.echo(
                "The '-r/--recursive' flag is not specified, "
                "will only search and unlock supported files in specified paths."
            )
    
    # print(params)
    
    tasks: Generator[tuple[str, str], None, None] = search_encrypted_files(*input_paths, recursive=recursively)
    
    last_exitcode = 0
    for filepath, encryption in tasks:
        try:
            audio_data, audiofmt, misc = unlock(filepath, encryption)
        except CLIError as exc:
            click.echo(str(exc), err=True)
            last_exitcode = 1
            continue
        else:
            last_exitcode = 0
        
        if os.path.isdir(output_path):
            save_filename: str = os.path.splitext(os.path.basename(filepath))[0] + '.' + audiofmt
            save_filepath: str = os.path.join(output_path, save_filename)
        else:
            save_filepath: str = output_path
        with open(save_filepath, 'w+b') as file:
            file.write(audio_data)
            file.seek(0, 0)
            
            if not without_metadata:
                embed_metadata(file, audiofmt, misc.get('metadata'), encryption=encryption)
            
            if not donot_print_ok:
                click.echo(
                    f"OK: ({encryption})'{filepath}' -> ({audiofmt})'{save_filepath}'"
                )
    
    exit(last_exitcode)
