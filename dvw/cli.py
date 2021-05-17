import click

from .analysis.report.commands import report
from .core.commands import embed, extract
from .analysis.attacks.commands import attack
from .analysis.metrics.commands import metric
from .analysis.probe.commands import probe


@click.group()
@click.help_option(
    "-h", "--help",
    help="Show this message and exit")
def cli():
    pass


cli.add_command(embed)
cli.add_command(extract)
cli.add_command(attack)
cli.add_command(metric)
cli.add_command(probe)
cli.add_command(report)
