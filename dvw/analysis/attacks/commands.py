import click
from click import IntRange, FloatRange

from .attacks import FlipAxis, RotateAngle, Flip, Crop, attack_video, Fill, Rotate, Gaussian, SaltAndPepper
from ...core.util.click import IgnoreRequiredWithHelp, update_context, default_help_context, EnumType


@click.group(
    help='Video file attacks',
    context_settings=default_help_context(),
    cls=IgnoreRequiredWithHelp)
@click.option(
    '-i', '--input', 'input_path',
    required=True,
    type=click.Path(exists=True),
    help='Input video file')
@click.option(
    '-o', '--output', 'output_path',
    required=True,
    type=click.Path(),
    help='Output video file')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.pass_context
def attack(ctx, **kwargs):
    update_context(ctx, **kwargs)


@attack.command()
@click.option(
    '--axis',
    required=True,
    type=EnumType(FlipAxis),
    help='Flip axis')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.pass_obj
def flip(group_args, axis):
    attack_video(Flip(axis), **group_args)


@attack.command()
@click.option(
    '-x',
    default=0,
    type=IntRange(min=0),
    help='The x coordinate of the first pixel in frame')
@click.option(
    '-y',
    default=0,
    type=IntRange(min=0),
    help='The y coordinate of the first pixel in frame')
@click.option(
    '--width',
    type=IntRange(min=0),
    help='New frame width')
@click.option(
    '--height',
    type=IntRange(min=0),
    help='New frame height')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.pass_obj
def crop(group_args, y, x, height, width):
    attack_video(Crop(y, x, height, width), **group_args)


@attack.command()
@click.option(
    '-x',
    default=0,
    type=IntRange(min=0),
    help='The x coordinate of the first pixel in frame')
@click.option(
    '-y',
    default=0,
    type=IntRange(min=0),
    help='The y coordinate of the first pixel in frame')
@click.option(
    '--width',
    required=True,
    type=IntRange(min=0),
    help='Shape width')
@click.option(
    '--height',
    required=True,
    type=IntRange(min=0),
    help='Shape height')
@click.option(
    '--value',
    default=0,
    type=IntRange(min=0, max=255),
    help='Fill value')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.pass_obj
def fill(group_args, y, x, height, width, value):
    attack_video(Fill(y, x, height, width, value), **group_args)


@attack.command()
@click.option(
    '--angle',
    required=True,
    type=EnumType(RotateAngle, int),
    help='Rotate angle')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.pass_obj
def rotate(group_args, angle):
    attack_video(Rotate(angle), **group_args)


@attack.command()
@click.option(
    '--std',
    required=True,
    type=FloatRange(min=0),
    help='Standard deviation of the distribution. Must be non-negative')
@click.option(
    '--area',
    default=1,
    type=FloatRange(min=0, max=1),
    help='Noise propagation area')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.pass_obj
def gaussian(group_args, std, area):
    attack_video(Gaussian(std, area), **group_args)


@attack.command()
@click.option(
    '--area',
    default=1,
    type=FloatRange(min=0, max=1),
    help='Noise propagation area')
@click.help_option(
    '-h', '--help',
    help='Show this message and exit')
@click.pass_obj
def salt_and_pepper(group_args, area):
    attack_video(SaltAndPepper(area), **group_args)
