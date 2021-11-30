from typing import Iterable, Any, Dict, List, Type

import click
from click import IntRange, FloatRange, Context, Option

from dvw.core.algorithms import (
    DwtWindowMedian,
    Algorithm,
    DwtDctEvenOddDifferential,
    DwtSvdMeanOverWindowEdges,
)
from dvw.core.methods import WindowPosition, Emphasis
from dvw.core.transforms import WaveletSubband
from dvw.io.watermark import WatermarkType
from dvw.ui.terminal import print_properties
from dvw.util.click import (
    EnumType,
    add_options,
    TransparentGroup,
    update_context,
)


_WAVELET_OPTIONS: List[Type[Option]] = [
    click.option("--wavelet", default="haar", help="Wavelet to use (default haar)"),
    click.option(
        "--level",
        default=1,
        metavar="INTEGER",
        type=IntRange(min=1),
        help="Wavelet decomposition level (must be > 0) (default 1)",
    ),
    click.option(
        "--subband",
        "subbands",
        multiple=True,
        type=EnumType(WaveletSubband, by_name=True),
        default=["LL"],
        help="Wavelet decomposition subband (default LL)",
    ),
    click.option(
        "--emphasis",
        default="capacity",
        type=EnumType(Emphasis),
        help="Watermark embedding emphasis (capacity)",
    ),
]


@click.group(help="Embedding watermark", cls=TransparentGroup)
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
    metavar="INTEGER",
    type=IntRange(min=0),
    help="New watermark width (relevant for bw-image type)",
)
@click.pass_context
def embed(ctx: Context) -> None:
    update_context(ctx, handler=_embed)


def _embed(
    algorithm: Algorithm,
    input_path: str,
    output_path: str,
    watermark_path: str,
    watermark_type: WatermarkType,
    **kwargs
) -> None:
    with watermark_type.reader(watermark_path, **kwargs) as watermark_reader:
        statistics = algorithm.embed(input_path, output_path, watermark_reader)
        print_properties(statistics, algorithm.__class__.__name__)


@click.group(help="Blind extracting watermark", cls=TransparentGroup)
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
    metavar="INTEGER",
    type=IntRange(min=0),
    help="New watermark width (relevant for bw-image type)",
)
@click.option(
    "-q", "--quantity", required=True, type=int, help="Number of extraction bits"
)
@click.pass_context
def extract(ctx: Context) -> None:
    update_context(ctx, handler=_extract)


def _extract(
    algorithm: Algorithm,
    input_path: str,
    watermark_path: str,
    watermark_type: WatermarkType,
    quantity: int,
    **kwargs
) -> None:
    with watermark_type.writer(watermark_path, **kwargs) as watermark_writer:
        statistics = algorithm.extract(input_path, watermark_writer, quantity)
        print_properties(statistics, algorithm.__class__.__name__)


@click.command(
    help="DWT window median (long version)",
    short_help="DWT window median",
)
@add_options(_WAVELET_OPTIONS)
@click.option(
    "--position",
    type=EnumType(WindowPosition),
    default=WindowPosition.HORIZONTAL,
    help="Window position (default hr)",
)
@click.option(
    "--window-size",
    default=3,
    metavar="INTEGER",
    type=IntRange(min=3),
    help="Window size (default 3)",
)
@click.pass_obj
def dwt_window_median(
    group_args: Dict[str, Any],
    wavelet: str,
    level: int,
    subbands: Iterable[WaveletSubband],
    position: WindowPosition,
    window_size: int,
    emphasis: Emphasis,
    **kwargs
) -> None:
    algorithm = DwtWindowMedian(
        wavelet, level, subbands, position, window_size, emphasis
    )
    group_args.pop("handler")(algorithm, **kwargs)


@click.command(
    help="DWT-DCT differential between even and odd components",
    short_help="DWT-DCT differential between even and odd components",
)
@add_options(_WAVELET_OPTIONS)
@click.option(
    "--offset",
    required=True,
    type=FloatRange(min=0, max=1),
    help="Offset coefficient",
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
    **kwargs
) -> None:
    algorithm = DwtDctEvenOddDifferential(
        wavelet, level, subbands, offset, area, repeats, alpha, emphasis
    )
    group_args.pop("handler")(algorithm, **kwargs)


@click.command(
    help="DWT-DCT differential between even and odd components",
    short_help="DWT-DCT differential between even and odd components",
)
@add_options(_WAVELET_OPTIONS)
@click.option("--window-size", type=IntRange(min=3), default=3, help="Window size")
@click.option("--alpha", required=True, type=float, help="Alpha coefficient")
@click.pass_obj
def dwt_svd_mean_over_window_edges(
    group_args: Dict[str, Any],
    wavelet: str,
    level: int,
    subbands: Iterable[WaveletSubband],
    window_size: int,
    alpha: float,
    emphasis: Emphasis,
    **kwargs
) -> None:
    algorithm = DwtSvdMeanOverWindowEdges(
        wavelet, level, subbands, window_size, alpha, emphasis
    )
    group_args.pop("handler")(algorithm, **kwargs)


embed.add_command(dwt_window_median)
extract.add_command(dwt_window_median)

embed.add_command(dwt_dct_even_odd_differential)
extract.add_command(dwt_dct_even_odd_differential)

embed.add_command(dwt_svd_mean_over_window_edges)
extract.add_command(dwt_svd_mean_over_window_edges)
