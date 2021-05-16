import click
from click import IntRange

from .video import VideoMetric, VideoComparator
from .watermark import WatermarkMetric, WatermarkComparator
from dvw.core.io import WatermarkType
from dvw.core.util.click import append_const, EnumType, update_context


@click.group(help='Calculate quality metrics between two files')
@click.option(
    '-p', '--precision',
    default=4,
    type=IntRange(min=0),
    help='Precision for decimal metric values')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.pass_context
def metric(ctx, **kwargs):
    update_context(ctx, **kwargs)


@metric.command(
    help='Calculate quality metrics between two video files (all metrics are enabled by default)',
    short_help='Calculate quality metrics between two video files')
@click.option(
    '--psnr',
    is_flag=True,
    callback=append_const('metrics', VideoMetric),
    help='Calculate PSNR (peak signal-to-noise ratio)')
@click.option(
    '--mssim',
    is_flag=True,
    callback=append_const('metrics', VideoMetric),
    help='Calculate MSSIM (mean structural similarity)')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.argument(
    'files', nargs=2,
    type=click.Path(exists=True))
@click.pass_obj
def video(group_args, **kwargs):
    comparator = VideoComparator(
        group_args['precision'],
        *kwargs.get('metrics', list(VideoMetric)))
    quality = comparator.compare(*kwargs['files'])
    print(quality)  # terminal.print_cmp(quality, 'Video Comparison')


@metric.command(
    help='Calculate quality metrics between two watermark files (all metrics are enabled by default)',
    short_help='Calculate quality metrics between two watermark files')
@click.option(
    '--ber',
    is_flag=True,
    callback=append_const('metrics', WatermarkMetric),
    help='Calculate BER (bit error rate)')
@click.option(
    '--nc',
    is_flag=True,
    callback=append_const('metrics', VideoMetric),
    help='Calculate NC (normalized correlation)')
@click.option(
    '-t', '--type', 'watermark_type',
    required=True,
    type=EnumType(WatermarkType),
    help='Type of watermark')
@click.option(
    '-W', '--width',
    type=IntRange(min=0),
    help='Watermark width (relevant for bw-image type)')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.argument(
    'files', nargs=2,
    type=click.Path(exists=True))
@click.pass_obj
def watermark(group_args, **kwargs):
    comparator = WatermarkComparator(
        group_args['precision'],
        *kwargs.get('metrics', list(WatermarkMetric)))
    quality = comparator.compare(*kwargs['files'], **kwargs)
    # quality = cmp_watermarks(*kwargs['files'], **kwargs)
    print(quality)  # terminal.print_cmp(quality, 'Watermark Comparison')
