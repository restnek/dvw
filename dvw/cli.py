import click

from . import io
from . import metrics
from . import probe
from . import terminal
from . import watermark
from .util import asplit


def validate_algorithm_options(ctx, param, value):
    try:
        algorithm = ctx.params['algorithm']
        rules = watermark.algorithm_options(algorithm)
        options = {k: rules[k](v) for k, v in asplit(value).items()}
        ctx.params.update(options)
        return value
    except ValueError:
        raise click.BadParameter(f'incorrect {param.human_readable_name}')


def append_const(option):
    def callback(ctx, param, value):
        if value:
            const = ctx.params.setdefault(option, [])
            const.append(param.human_readable_name)
        return value
    return callback


@click.group()
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
def cli():
    pass


@cli.command(
    help='Show media and codec information',
    short_help='Show media and codec information')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.argument('file')
def info(file):
    format_, streams, metadata = probe.probe(file)
    terminal.print_probe(format_, streams, metadata)


@cli.command(
    help='Show quality metrics between two video files (all metrics are enabled by default)',
    short_help='Show quality metrics between two video files')
@click.option(
    '--psnr',
    is_flag=True,
    callback=append_const('metrics'),
    help='Calculate PSNR (peak signal-to-noise ratio)')
@click.option(
    '--mssim',
    is_flag=True,
    callback=append_const('metrics'),
    help='Calculate MSSIM (mean structural similarity)')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.argument(
    'files', nargs=2,
    type=click.Path(exists=True))
def video_compare(**kwargs):
    quality = metrics.cmp_video(*kwargs['files'], kwargs.get('metrics'))
    terminal.print_cmp(quality, 'Video Comparison')


@cli.command(
    help='Show BER (bit error rate) between two watermark files',
    short_help='Show BER (bit error rate) between two watermark files')
@click.option(
    '-t', '--type', 'wmtype',
    required=True,
    type=click.Choice(['image', 'text'], case_sensitive=False),
    help='Type of watermark')
@click.option(
    '--width',
    type=int,
    help='New watermark width (relevant for image type)')
@click.argument(
    'files', nargs=2,
    type=click.Path(exists=True))
def ber(**kwargs):
    total, errors, quality = metrics.ber(
        *kwargs['files'],
        kwargs['wmtype'],
        kwargs.get('width'))
    terminal.print_cmp(
        [('total', total), ('errors', errors), ('ber', quality)],
        'Watermark Comparison')


@cli.command(
    help='Embedding watermark',
    short_help='Embedding watermark')
@click.option(
    '-a', '--algorithm',
    required=True,
    metavar='TEXT',
    type=click.Choice(watermark.algorithms(), case_sensitive=False),
    help='Watermark embedding algorithm')
@click.option(
    '--algopt',
    multiple=True,
    metavar='OPT:VALUE',
    callback=validate_algorithm_options,
    help='Set algorithm options as opt:value')
@click.option(
    '-w', '--watermark', 'wmpath',
    required=True,
    type=click.Path(exists=True),
    help='input watermark file')
@click.option(
    '-t', '--type', 'wmtype',
    required=True,
    type=click.Choice(['image', 'text'], case_sensitive=False),
    help='Type of watermark')
@click.option(
    '--width',
    type=int,
    help='New watermark width (relevant for image type)')
@click.option(
    '-i', '--input', 'video_path',
    required=True,
    type=click.Path(exists=True),
    help='Input video file')
@click.option(
    '-o', '--output', 'wmvideo_path',
    required=True,
    type=click.Path(),
    help='Output video file')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
def embed(**kwargs):
    embedded = watermark.embed(**kwargs)
    print(embedded)  # replace with print method from terminal


@cli.command(
    help='Blind extracting watermark',
    short_help='Blind extracting watermark')
@click.option(
    '-a', '--algorithm',
    required=True,
    metavar='TEXT',
    type=click.Choice(watermark.algorithms(), case_sensitive=False),
    help='Watermark extracting algorithm')
@click.option(
    '--algopt',
    multiple=True,
    metavar='OPT:VALUE',
    callback=validate_algorithm_options,
    help='Set algorithm options as opt:value')
@click.option(
    '-q', '--quantity',
    required=True,
    type=int,
    help='Number of extraction bits')
@click.option(
    '-i', '--input', 'wmvideo_path',
    required=True,
    type=click.Path(exists=True),
    help='Input video file')
@click.option(
    '-o', '--output', 'wmpath',
    required=True,
    type=click.Path(),
    help='Output watermark file')
@click.option(
    '-t', '--type', 'wmtype',
    required=True,
    type=click.Choice(io.types(), case_sensitive=False),
    help='Type of watermark')
@click.option(
    '--width',
    type=int,
    help='New watermark width (relevant for image type)')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
def extract(**kwargs):
    watermark.extract(**kwargs)
