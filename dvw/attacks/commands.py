import click
from click import IntRange, FloatRange

from dvw.attacks import (
    FlipAxis,
    RotateAngle,
    Flip,
    Crop,
    attack_video,
    Fill,
    Rotate,
    Gaussian,
    SaltAndPepper,
)
from dvw.util.click import (
    EnumType,
    TransparentGroup,
)


@click.group(help="Video file attacks", cls=TransparentGroup)
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
def attack() -> None:
    pass


@attack.command()
@click.option("--axis", required=True, type=EnumType(FlipAxis), help="Flip axis")
def flip(axis: FlipAxis, **kwargs) -> None:
    attack_video(Flip(axis), **kwargs)


@attack.command()
@click.option(
    "-x",
    default=0,
    type=IntRange(min=0),
    help="The x coordinate of the first pixel in frame",
)
@click.option(
    "-y",
    default=0,
    type=IntRange(min=0),
    help="The y coordinate of the first pixel in frame",
)
@click.option("--width", type=IntRange(min=0), help="New frame width")
@click.option("--height", type=IntRange(min=0), help="New frame height")
def crop(y: int, x: int, height: int, width: int, **kwargs) -> None:
    attack_video(Crop(y, x, height, width), **kwargs)


@attack.command(
    help="Fill the selected area of the frame with the specified value",
)
@click.option(
    "-x",
    default=0,
    metavar="INTEGER",
    type=IntRange(min=0),
    help="The x coordinate of the first pixel in frame (default 0)",
)
@click.option(
    "-y",
    default=0,
    metavar="INTEGER",
    type=IntRange(min=0),
    help="The y coordinate of the first pixel in frame (default 0)",
)
@click.option(
    "--width",
    required=True,
    metavar="INTEGER",
    type=IntRange(min=0),
    help="Shape width",
)
@click.option(
    "--height",
    required=True,
    metavar="INTEGER",
    type=IntRange(min=0),
    help="Shape height",
)
@click.option(
    "--value",
    default=0,
    metavar="INTEGER",
    type=IntRange(min=0, max=255),
    help="Fill value (default 0)",
)
def fill(y: int, x: int, height: int, width: int, value: int, **kwargs) -> None:
    attack_video(Fill(y, x, height, width, value), **kwargs)


@attack.command()
@click.option("--angle", required=True, type=float, help="Rotate angle")
def rotate(angle: float, **kwargs) -> None:
    attack_video(Rotate(angle), **kwargs)


@attack.command()
@click.option(
    "--std",
    required=True,
    type=FloatRange(min=0),
    help="Standard deviation of the distribution. Must be non-negative",
)
@click.option(
    "--area", default=1, type=FloatRange(min=0, max=1), help="Noise propagation area"
)
def gaussian(std: float, area: float, **kwargs) -> None:
    attack_video(Gaussian(std, area), **kwargs)


@attack.command()
@click.option(
    "--area", default=1, type=FloatRange(min=0, max=1), help="Noise propagation area"
)
def salt_and_pepper(area: float, **kwargs) -> None:
    attack_video(SaltAndPepper(area), **kwargs)
