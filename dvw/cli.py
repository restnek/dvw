import click

from dvw.attacks.commands import attack

from dvw.core.commands import embed, extract
from dvw.metrics.commands import metric
from dvw.probe.commands import probe
from dvw.report.commands import report


@click.group()
@click.help_option("-h", "--help", help="Show this message and exit")
def cli():
    pass


cli.add_command(embed)
cli.add_command(extract)
cli.add_command(attack)
cli.add_command(metric)
cli.add_command(probe)
cli.add_command(report)
