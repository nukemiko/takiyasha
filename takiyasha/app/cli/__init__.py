import os
import sys

import click

from .files import get_input_paths, get_output_path
from ... import VERSION


def _print_supported_format(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('Supported encryption formats:')
    click.echo(
        """\u3000\u3000- NCM files (.ncm)
\u3000\u3000- QMCv1 files (.qmcflac/.qmcogg/.qmc0/.qmc2/.qmc3/.qmc4/.qmc6/.qmc8)
\u3000\u3000- QMCv2 files (.mflac/.mflac0/.mgg/.mgg0/.mgg1/.mggl)
\u3000\u3000- Moo Music format files (.bkcmp3/.bkcflac/.bkc*/...)"""
    )
    ctx.exit()


def _print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f'Takiyasha version {VERSION} (Python {sys.version} on {sys.platform})')
    click.echo(f"Use '--support-exts' or '--support-formats' to see support encryption formats.")
    ctx.exit()


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option(
    '-o', '--output', 'path_to_output', metavar='<PATH>', default=os.getcwd(),
    type=click.Path(exists=True),
    show_default=os.getcwd(),
    help="""\b
    Path to output file or dir."""
)
@click.option(
    '-r', '--recursive', is_flag=True, show_default='False',
    help="""If there is a directory in <PATHS TO INPUT...>, recursively process the supported files in the directory.
    
    Enabled by default when there is only one directory in <PATHS TO INPUT...>."""
)
@click.option(
    '--supported-exts', '--supported-formats', is_flag=True, callback=_print_supported_format,
    expose_value=False, is_eager=True,
    help="""Show supported file extensions and exit."""
)
@click.option(
    '-V', '--version', is_flag=True, callback=_print_version,
    expose_value=False, is_eager=True
)
@click.argument('path_to_input', metavar='<PATHS TO INPUT...>', type=click.Path(exists=True), nargs=-1)
def main(**params):
    """\b
    Takiyasha - Unlock DRM protected music file(s).
    
    Get the latest version: https://github.com/nukemiko/takiyasha
    
    \b
    WARNING: The command line has no function now. Please wait for future updates."""
    click.echo("""\033[31;1mThe command line has no function now. Please wait for future updates.\033[0m""")
    click.echo("""\033[32;1mGet the latest version: https://github.com/nukemiko/takiyasha\033[0m""")
