from typing import Dict, Any, Iterable

import click
from click import IntRange, Choice, FloatRange
from pywt import wavelist

from .algorithms import (
    DwtWindowMedian,
    Algorithm,
    DwtDctEvenOddDifferential,
    DwtSvdMeanOverWindowEdges,
)
from .core import EmbeddingStatistics, ExtractingStatistics
from .io import WatermarkType
from .methods import WindowPosition, Emphasis
from .transforms import WaveletSubband
from .util.click import (
    IgnoreRequiredWithHelp,
    update_context,
    EnumType,
    default_help_context,
)
from ..ui.terminal import print_properties


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
    update_context(ctx, **kwargs, handler=_embed)


def _embed(
    algorithm: Algorithm,
    input_path: str,
    output_path: str,
    watermark_path: str,
    watermark_type: WatermarkType,
    **kwargs: Any
) -> EmbeddingStatistics:
    with watermark_type.reader(watermark_path, **kwargs) as watermark_reader:
        return algorithm.embed(input_path, output_path, watermark_reader)


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
    update_context(ctx, **kwargs, handler=_extract)


def _extract(
    algorithm: Algorithm,
    input_path: str,
    watermark_path: str,
    watermark_type: WatermarkType,
    quantity: int,
    **kwargs: Any
) -> ExtractingStatistics:
    with watermark_type.writer(watermark_path, **kwargs) as watermark_writer:
        return algorithm.extract(input_path, watermark_writer, quantity)


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
def dwt_window_median(
    group_args: Dict[str, Any],
    wavelet: str,
    level: int,
    subbands: Iterable[WaveletSubband],
    position: WindowPosition,
    window_size: int,
    emphasis: Emphasis,
    **kwargs: Any
) -> None:
    algorithm = DwtWindowMedian(
        wavelet, level, subbands, position, window_size, emphasis
    )
    statistics = group_args.pop("handler")(algorithm, **group_args, **kwargs)
    print_properties(statistics, "dwt-window-median")


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
def dwt_dct_even_odd_differential(
    group_args: Dict[str, Any],
    wavelet: str,
    level: int,
    subbands: Iterable[WaveletSubband],
    offset: float,
    area: float,
    repeats: int,
    alpha: float,
    emphasis: Emphasis,
    **kwargs: Any
):
    algorithm = DwtDctEvenOddDifferential(
        wavelet, level, subbands, offset, area, repeats, alpha, emphasis
    )
    statistics = group_args.pop("handler")(algorithm, **group_args, **kwargs)
    print_properties(statistics, "dwt-dct-even-odd-differential")


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
def dwt_svd_mean_over_window_edges(
    group_args: Dict[str, Any],
    wavelet: str,
    level: int,
    subbands: Iterable[WaveletSubband],
    window_size: int,
    alpha: float,
    emphasis: Emphasis,
    **kwargs: Any
):
    algorithm = DwtSvdMeanOverWindowEdges(
        wavelet, level, subbands, window_size, alpha, emphasis
    )
    statistics = group_args.pop("handler")(algorithm, **group_args, **kwargs)
    print_properties(statistics, "dwt-svd-mean-over-window-edges")


embed.add_command(dwt_window_median)
extract.add_command(dwt_window_median)

embed.add_command(dwt_dct_even_odd_differential)
extract.add_command(dwt_dct_even_odd_differential)

embed.add_command(dwt_svd_mean_over_window_edges)
extract.add_command(dwt_svd_mean_over_window_edges)
