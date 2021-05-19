from dataclasses import dataclass
from typing import Callable, Any, List, Optional, Dict, Tuple, Iterable

import ffmpeg

from dvw.util import filename
from dvw.util.unit import bitrate2human, size2human, seconds2human


@dataclass
class ProbeField:
    name: str
    label: str
    handler: Optional[Callable[[str], Any]] = None


@dataclass
class VideoProbe:
    format: Dict[str, Any]
    streams: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]


def probe(path: str) -> VideoProbe:
    info = ffmpeg.probe(path)
    format_, metadata = _parse_format(info["format"])
    streams = _parse_all_streams(info["streams"])
    return VideoProbe(format_, streams, metadata)


def _parse_format(format_: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    metadata = None
    if "tags" in format_:
        metadata = {k: v for k, v in format_["tags"].items()}
    format_ = _parse_all_fields(format_, _FORMAT_FIELDS)
    return format_, metadata


def _parse_all_streams(streams: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [_parse_all_fields(s, _STREAM_FIELDS[s["codec_type"]]) for s in streams]


def _parse_all_fields(
    data: Dict[str, Any], fields: Iterable[ProbeField]
) -> Dict[str, Any]:
    return {f.label: _parse_field(data, f) for f in fields if f.name in data}


def _parse_field(data: Dict[str, Any], field: ProbeField) -> str:
    value = data[field.name]
    return field.handler(value) if field.handler else value


def _parse_size(size) -> str:
    return size2human(float(size))


def _parse_bitrate(bitrate) -> str:
    return bitrate2human(float(bitrate))


def _parse_duration(duration) -> str:
    return seconds2human(float(duration))


_FORMAT_FIELDS: List[ProbeField] = [
    ProbeField("filename", "Filename", filename),
    ProbeField("format_long_name", "Format name"),
    ProbeField("size", "Size", _parse_size),
    ProbeField("bit_rate", "Bitrate", _parse_bitrate),
    ProbeField("nb_streams", "Streams"),
]

_STREAM_FIELDS = {
    "video": [
        ProbeField("codec_type", "Codec type"),
        ProbeField("codec_long_name", "Codec name"),
        ProbeField("width", "Width"),
        ProbeField("height", "Height"),
        ProbeField("r_frame_rate", "Frame rate"),
        ProbeField("duration", "Duration", _parse_duration),
        ProbeField("bit_rate", "Bit rate", _parse_bitrate),
        ProbeField("nb_frames", "Number of frames"),
    ],
    "audio": [
        ProbeField("codec_type", "Codec type"),
        ProbeField("codec_long_name", "Codec name"),
        ProbeField("sample_rate", "Sample rate"),
        ProbeField("channels", "Channels"),
        ProbeField("bit_rate", "Bit rate", _parse_bitrate),
    ],
}
