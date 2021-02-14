import ntpath
from datetime import timedelta

import ffmpeg

from .util import bitrate2human, get, size2human


def probe(path):
    info = ffmpeg.probe(path)
    format_, metadata = _parse_format(info['format'])
    streams = _parse_all_streams(info['streams'])
    return format_, streams, metadata


def _parse_format(format_):
    metadata = format_['tags'].items() if 'tags' in format_ else None
    format_ = _parse_all_fields(format_, _FORMAT_FIELDS)
    return format_, metadata


def _parse_all_streams(streams):
    return [
        _parse_all_fields(s, _STREAM_FIELDS[s['codec_type']])
        for s in streams
    ]


def _parse_all_fields(data, fields):
    return [_parse_field(data, *f) for f in fields if f[0] in data]


def _parse_field(data, field, label=None, handler=None):
    value = data[field]
    value = handler(value) if handler else value
    label = get(label, field)
    return label, value


_FORMAT_FIELDS = [
    (
        'filename',
        'Filename',
        lambda f: ntpath.split(f)[1]
    ),
    ('format_long_name', 'Format name'),
    (
        'size',
        'Size',
        lambda s: size2human(float(s))
    ),
    (
        'bit_rate',
        'Bitrate',
        lambda b: bitrate2human(float(b))
    ),
    ('nb_streams', 'Streams'),
]

_STREAM_FIELDS = {
    'video': [
        ('codec_type', 'Codec type'),
        ('codec_long_name', 'Codec name'),
        ('width', 'Width'),
        ('height', 'Height'),
        ('r_frame_rate', 'Frame rate'),
        (
            'duration',
            'Duration',
            lambda s: timedelta(seconds=int(float(s)))
        ),
        (
            'bit_rate',
            'Bit rate',
            lambda b: bitrate2human(float(b))
        ),
        ('nb_frames', 'Number of frames'),
    ],
    'audio': [
        ('codec_type', 'Codec type'),
        ('codec_long_name', 'Codec name'),
        ('sample_rate', 'Sample rate'),
        ('channels', 'Channels'),
        (
            'bit_rate',
            'Bit rate',
            lambda b: bitrate2human(float(b))
        ),
    ],
}
