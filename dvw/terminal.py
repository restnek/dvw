from rich import box, print
from rich.console import RenderGroup
from rich.panel import Panel
from rich.table import Column, Table
from rich.text import Text

from .util import around


class PropPanel(Panel):
    def __init__(
            self,
            rows,
            subrows=None,
            title=None,
            title_align='center',
            expand=False):

        renderable = PropTable(rows)

        if subrows:
            subpanels = [
                PropPanel(r, title=t, title_align='left', expand=True)
                for t, r in subrows
            ]
            renderable = RenderGroup(renderable, *subpanels)

        super().__init__(
            renderable,
            title=title,
            title_align=title_align,
            expand=expand)


class PropTable(Table):
    def __init__(self, rows):
        super().__init__(
            box=box.MINIMAL,
            show_header=False,
            show_edge=False,
            expand=False)

        for r in rows:
            super().add_row(*map(str, r))


class ComparisonPanel(Panel):
    def __init__(self, headers, rows, title=None, title_align='center'):
        table = ComparisonTable(headers, rows)
        super().__init__(
            table,
            title=title,
            title_align=title_align,
            expand=False)


class ComparisonTable(Table):
    def __init__(self, headers, rows):
        super().__init__(
            box=box.MINIMAL,
            show_edge=False,
            expand=False)

        super().add_column(style='bold')
        for h in headers:
            super().add_column(Text(h, justify='center'))

        for r in rows:
            super().add_row(*map(str, r))


def print_probe(format_, streams, metadata=None):
    subrows = [['Meta', metadata]] if metadata else None
    print(PropPanel(format_, subrows, 'Format'))

    for i, stream in enumerate(streams):
        print()
        print(PropPanel(stream, title=f'Stream {i}'))


def print_cmp(quality, title='Comparison', precise=None):
    # if precise:
    #     quality = around(quality, precise)
    panel = ComparisonPanel(['Value'], quality, title)
    print(panel)