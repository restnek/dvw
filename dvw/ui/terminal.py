from typing import Optional, Any, Dict, Iterable

from rich import box, print
from rich.align import AlignValues
from rich.columns import Columns
from rich.console import RenderGroup, RenderableType
from rich.panel import Panel
from rich.table import Table

from dvw.analysis.metrics import MetricValue
from dvw.analysis.probe import VideoProbe
from dvw.core.util.base import PrettyDictionary


class PropertyPanel(Panel):
    def __init__(
        self,
        data: Dict[str, Any] = None,
        title: Optional[str] = None,
        title_align: AlignValues = "center",
        expand: bool = False,
    ) -> None:
        self.table = PropertyTable(data)
        self.group = RenderGroup(self.table)
        super().__init__(
            self.group, title=title, title_align=title_align, expand=expand
        )

    def add_row(self, property_: str, value: Any) -> None:
        self.table.add_row(property_, str(value))

    def add_section(self, renderable: RenderableType) -> None:
        self.group.renderables.append(renderable)


class PropertyTable(Table):
    def __init__(self, data: Dict[str, Any]) -> None:
        super().__init__(
            box=box.MINIMAL, show_header=False, show_edge=False, expand=False
        )
        if data:
            for k, v in data.items():
                super().add_row(k, str(v))


def print_properties(data: PrettyDictionary, title: Optional[str] = None) -> None:
    panel = PropertyPanel(data.dictionary(), title)
    print(panel)


def print_probe(probe: VideoProbe) -> None:
    format_panel = PropertyPanel(probe.format, "Format", expand=True)
    if probe.metadata:
        format_panel.add_section(PropertyPanel(probe.metadata, "Metadata", expand=True))

    stream_group = RenderGroup()
    for i, stream in enumerate(probe.streams, 1):
        stream_group.renderables.append(
            PropertyPanel(stream, f"Stream {i}", expand=True)
        )

    print(Columns([format_panel, stream_group]))


def print_metrics(metrics: Iterable[MetricValue]) -> None:
    pass
