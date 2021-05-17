import click
from click import IntRange, Choice, FloatRange
from pywt import wavelist

from . import algorithms
from .io import WatermarkType
from .methods import WindowPosition, Emphasis
from .transforms import WaveletSubband
from .util.click import (
    IgnoreRequiredWithHelp,
    update_context,
    EnumType,
    default_help_context,
)


@click.group(
    help="Embedding watermark",
    context_settings=default_help_context(),
    cls=IgnoreRequiredWithHelp,
)
@click.option(
    "-i",
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True),
    help="Input video file",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    required=True,
    type=click.Path(),
    help="Output video file",
)
@click.option(
    "-w",
    "--watermark",
    "watermark_path",
    required=True,
    type=click.Path(exists=True),
    help="Input watermark file",
)
@click.option(
    "-t",
    "--type",
    "watermark_type",
    required=True,
    type=EnumType(WatermarkType),
    help="Type of watermark",
)
@click.option(
    "-W",
    "--width",
    type=IntRange(min=0),
    help="New watermark width (relevant for bw-image type)",
)
@click.help_option("-h", "--help", help="Show this message and exit")
@click.pass_context
def embed(ctx, **kwargs):
    update_context(ctx, **kwargs, mode=algorithms.Mode.EMBED)


@click.group(
    help="Blind extracting watermark",
    context_settings=default_help_context(),
    cls=IgnoreRequiredWithHelp,
)
@click.option(
    "-i",
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True),
    help="Input video file",
)
@click.option(
    "-o",
    "--output",
    "watermark_path",
    required=True,
    type=click.Path(),
    help="Output watermark file",
)
@click.option(
    "-t",
    "--type",
    "watermark_type",
    required=True,
    type=EnumType(WatermarkType),
    help="Type of watermark",
)
@click.option(
    "-W",
    "--width",
    type=IntRange(min=0),
    help="New watermark width (relevant for bw-image type)",
)
@click.option(
    "-q", "--quantity", required=True, type=int, help="Number of extraction bits"
)
@click.help_option("-h", "--help", help="Show this message and exit")
@click.pass_context
def extract(ctx, **kwargs):
    update_context(ctx, **kwargs, mode=algorithms.Mode.EXTRACT)


@click.command(help="DWT window median", short_help="DWT window median")
@click.option(
    "--wavelet", type=Choice(wavelist()), default="haar", help="Wavelet to use"
)
@click.option(
    "--level",
    type=IntRange(min=0),
    default=1,
    help="Wavelet decomposition level (must be >= 0)",
)
@click.option(
    "--subband",
    "subbands",
    multiple=True,
    type=EnumType(WaveletSubband, by_name=True),
    default=["LL"],
    help="Wavelet decomposition subband",
)
@click.option(
    "--position",
    type=EnumType(WindowPosition),
    default=WindowPosition.HORIZONTAL,
    help="Window position",
)
@click.option("--window-size", type=IntRange(min=3), default=3, help="Window size")
@click.option(
    "--emphasis",
    type=EnumType(Emphasis),
    default="capacity",
    help="Watermark embedding emphasis",
)
@click.help_option("-h", "--help", help="Show this message and exit")
@click.pass_obj
def dwt_window_median(group_args, **kwargs):
    result = algorithms.dwt_window_median(**group_args, **kwargs)
    print(result)


@click.command(
    help="DWT-DCT differential between even and odd components",
    short_help="DWT-DCT differential between even and odd components",
)
@click.option(
    "--wavelet", type=Choice(wavelist()), default="haar", help="Wavelet to use"
)
@click.option(
    "--level",
    type=IntRange(min=0),
    default=1,
    help="Wavelet decomposition level (must be >= 0)",
)
@click.option(
    "--subband",
    "subbands",
    multiple=True,
    type=EnumType(WaveletSubband, by_name=True),
    default=["LL"],
    help="Wavelet decomposition coefficient",
)
@click.option(
    "--offset", required=True, type=FloatRange(min=0, max=1), help="Offset coefficient"
)
@click.option(
    "--area", required=True, type=FloatRange(min=0, max=1), help="Area coefficient"
)
@click.option(
    "--repeats",
    default=1,
    type=IntRange(min=1),
    help="Number of times of bit embedding/extraction",
)
@click.option("--alpha", required=True, type=float, help="Alpha coefficient")
@click.option(
    "--emphasis",
    type=EnumType(Emphasis),
    default="capacity",
    help="Watermark embedding emphasis",
)
@click.help_option("-h", "--help", help="Show this message and exit")
@click.pass_obj
def dwt_dct_even_odd_differential(group_args, **kwargs):
    result = algorithms.dwt_dct_even_odd_differential(**group_args, **kwargs)
    print(result)


@click.command(
    help="DWT-DCT differential between even and odd components",
    short_help="DWT-DCT differential between even and odd components",
)
@click.option(
    "--wavelet", type=Choice(wavelist()), default="haar", help="Wavelet to use"
)
@click.option(
    "--level",
    type=IntRange(min=0),
    default=1,
    help="Wavelet decomposition level (must be >= 0)",
)
@click.option(
    "--subband",
    "subbands",
    multiple=True,
    type=EnumType(WaveletSubband, by_name=True),
    default=["LL"],
    help="Wavelet decomposition coefficient",
)
@click.option("--window-size", type=IntRange(min=3), default=3, help="Window size")
@click.option("--alpha", required=True, type=float, help="Alpha coefficient")
@click.option(
    "--emphasis",
    type=EnumType(Emphasis),
    default="capacity",
    help="Watermark embedding emphasis",
)
@click.help_option("-h", "--help", help="Show this message and exit")
@click.pass_obj
def dwt_svd_mean_over_window_edges(group_args, **kwargs):
    result = algorithms.dwt_svd_mean_over_window_edges(**group_args, **kwargs)
    print(result)


embed.add_command(dwt_window_median)
extract.add_command(dwt_window_median)

embed.add_command(dwt_dct_even_odd_differential)
extract.add_command(dwt_dct_even_odd_differential)

embed.add_command(dwt_svd_mean_over_window_edges)
extract.add_command(dwt_svd_mean_over_window_edges)
