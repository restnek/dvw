from typing import Iterable, Optional

import click
from click import IntRange

from dvw.io.watermark import WatermarkType
from dvw.metrics.video import VideoMetric, VideoComparator
from dvw.metrics.watermark import WatermarkMetric, WatermarkComparator
from dvw.ui.terminal import print_metrics
from dvw.util.click import EnumType, TransparentGroup, append_flag


@click.group(help="Calculate quality metrics between two files", cls=TransparentGroup)
@click.option(
    "-p",
    "--precision",
    default=4,
    type=IntRange(min=0),
    help="Precision for decimal metric values",
)
def metric() -> None:
    pass


@metric.command(
    help="Calculate quality metrics between two video files (all metrics are enabled by default)",
    short_help="Calculate quality metrics between two video files",
)
@click.option(
    "--psnr",
    is_flag=True,
    callback=append_flag("metrics", VideoMetric),
    help="Calculate PSNR (peak signal-to-noise ratio)",
)
@click.option(
    "--mssim",
    is_flag=True,
    callback=append_flag("metrics", VideoMetric),
    help="Calculate MSSIM (mean structural similarity)",
)
@click.argument("files", nargs=2, type=click.Path(exists=True))
def video(
    precision: int,
    files: Iterable[str],
    metrics: Optional[Iterable[VideoMetric]] = None,
) -> None:
    metrics = metrics or list(VideoMetric)
    comparator = VideoComparator(precision, *metrics)
    metrics = comparator.compare(*files)
    print_metrics(metrics)


@metric.command(
    help="Calculate quality metrics between two watermark files (all metrics are enabled by default)",
    short_help="Calculate quality metrics between two watermark files",
)
@click.option(
    "--ber",
    is_flag=True,
    callback=append_flag("metrics", WatermarkMetric),
    help="Calculate BER (bit error rate)",
)
@click.option(
    "--nc",
    is_flag=True,
    callback=append_flag("metrics", WatermarkMetric),
    help="Calculate NC (normalized correlation)",
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
    help="Watermark width (relevant for bw-image type)",
)
@click.argument("files", nargs=2, type=click.Path(exists=True))
def watermark(
    precision: int,
    files: Iterable[str],
    metrics: Optional[Iterable[WatermarkMetric]] = None,
    **kwargs
) -> None:
    metrics = metrics or list(WatermarkMetric)
    comparator = WatermarkComparator(precision, *metrics)
    metrics = comparator.compare(*files, **kwargs)
    print_metrics(metrics)
