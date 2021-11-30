import click
from click import IntRange

from dvw.report import HtmlReport
from dvw.report.brute import BruteForce
from dvw.report.config import config2kit


@click.command(help="Generate report")
@click.option(
    "-c", "--config", type=click.Path(exists=True), help="Config file with settings"
)
@click.option(
    "-o",
    "--output",
    "output_path",
    required=True,
    type=click.Path(),
    help="Output directory",
)
@click.option(
    "-p",
    "--precision",
    default=4,
    metavar="INTEGER",
    type=IntRange(min=0),
    help="Precision for decimal metric values (default 4)",
)
def report(config, output_path, precision):
    kit = config2kit(config)
    report_ = HtmlReport(output_path, "exp", "assets", "result.json")
    bf = BruteForce(kit, precision)
    bf.start(report_)
