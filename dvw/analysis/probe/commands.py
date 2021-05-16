import click

from .probe import probe as probe_


@click.command(
    help='Show media and codec information',
    short_help='Show media and codec information')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.argument('file', type=click.Path(exists=True))
def probe(file):
    result = probe_(file)
    print(result)
    # format_, streams, metadata = probe.probe(file)
    # terminal.print_probe(format_, streams, metadata)
