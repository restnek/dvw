import click

from dvw.report import HtmlReport
from dvw.report.brute import BruteForce
from dvw.report.config import config2kit


@click.group(help="Generate report")
@click.help_option("-h", "--help", help="Show this message and exit")
def report():
    pass


@report.command(
    help="Start generating the report", short_help="Start generating the report"
)
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
@click.help_option("-h", "--help", help="Show this message and exit")
def start(config, output_path):
    precision = 4
    kit = config2kit(config)
    report_ = HtmlReport(output_path, "exp", "assets", "result.json")
    bf = BruteForce(kit, precision)
    bf.start(report_)


@report.command()
@click.option("-s", "--session", type=click.Path(exists=True), help="Session path")
def resume(**kwargs):
    print(kwargs)
