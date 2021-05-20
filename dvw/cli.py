import click

from dvw.attacks.commands import attack

from dvw.core.commands import embed, extract
from dvw.metrics.commands import metric
from dvw.probe.commands import probe
from dvw.report.commands import report


@click.group()
@click.help_option("-h", "--help", help="Show this message and exit")
def main():
    pass


main.add_command(embed)
main.add_command(extract)
main.add_command(attack)
main.add_command(metric)
main.add_command(probe)
main.add_command(report)
