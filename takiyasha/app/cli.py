import os
import sys

import click

from .. import VERSION


def _print_supported_format(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('Supported encryption format:')
    click.echo(
        """
        - NCM file (.ncm)
        - QMCv1 (.qmc0/.qmc2/.qmc3/.qmcflac/.qmcogg)
        - QMCv2 (.mflac/.mgg/.mflac0/.mgg1/.mggl)
        - Some files that require your luck
            - Moo Music format (.bkcmp3/.bkcflac/...)
            - QQMusic Tm format (.tm0/.tm2/.tm3/.tm6)
            - QQMusic oversea / JOOX Music (.ofl_en)"""
    )
    ctx.exit()


def _print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f'Takiyasha version {VERSION} (Running on Python {sys.version})')
    ctx.exit()


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option(
    '-o', '--output', 'path_to_output', metavar='<PATH>', default=os.getcwd(),
    type=click.Path(exists=True),
    show_default='current directory',
    help="""\b
    Path to output file or dir."""
)
@click.option(
    '-s', '--source', '--source-platform', 'source_platform', type=click.Choice(
        ['cloudmusic', 'qqmusic'], case_sensitive=False
    ),
    help="""\b
    The name of the platform you downloaded the file from (cloudmusic, qqmusic, ...)"""
)
@click.option(
    '--supported-ext', '--supported-format', is_flag=True, callback=_print_supported_format,
    expose_value=False, is_eager=True,
    help="""Show supported file extensions and exit"""
)
@click.option(
    '-V', '--version', is_flag=True, callback=_print_version,
    expose_value=False, is_eager=True
)
@click.argument('path_to_input', metavar='<PATH TO INPUT>', type=click.Path(exists=True))
def main(**params):
    """\b
    Takiyasha - Unlock DRM protected music file(s).
    
    Get the latest version: https://github.com/nukemiko/takiyasha
    
    \b
    WARNING: The command line has no function now. Please wait for future updates."""
    click.echo("""\033[31;1mThe command line has no function now. Please wait for future updates.\033[0m""")
    click.echo("""\033[32;1mGet the latest version: https://github.com/nukemiko/takiyasha\033[0m""")
