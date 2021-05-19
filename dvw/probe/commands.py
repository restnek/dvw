import click

from dvw.probe import probe as probe_
from dvw.ui.terminal import print_probe


@click.command(
    help="Show media and codec information",
    short_help="Show media and codec information",
)
@click.help_option("-h", "--help", help="Show this message and exit")
@click.argument("file", type=click.Path(exists=True))
def probe(file):
    video_probe = probe_(file)
    print_probe(video_probe)
