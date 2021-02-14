import cv2
import numpy as np
from skimage.metrics import structural_similarity

from .io import create_reader
from .util import get

_VIDEO_METRICS = {
    'psnr': cv2.PSNR,
    'mssim': lambda f1, f2: structural_similarity(f1, f2, multichannel=True),
}


def psnr(filename1, filename2):
    return cmp_video(filename1, filename2, ('psnr',))[0][1]


def mssim(filename1, filename2):
    return cmp_video(filename1, filename2, ('mssim',))[0][1]


def cmp_video(filename1, filename2, metrics=None):
    metrics = _get_video_metrics(metrics)
    if not metrics:
        return []

    vcap1 = cv2.VideoCapture(filename1)
    vcap2 = cv2.VideoCapture(filename2)

    quality = _cmp_frames(vcap1, vcap2, metrics)

    vcap1.release()
    vcap2.release()

    return quality


def _get_video_metrics(metrics):
    metrics = get(metrics, ['psnr', 'mssim'])
    return [(m, _VIDEO_METRICS[m]) for m in metrics if m in _VIDEO_METRICS]


def _cmp_frames(vcap1, vcap2, metrics):
    cnt = 0
    total = np.zeros(len(metrics))

    success1, frame1 = vcap1.read()
    success2, frame2 = vcap2.read()
    while success1 and success2:
        total += _calc_metrics(frame1, frame2, metrics)
        cnt += 1
        success1, frame1 = vcap1.read()
        success2, frame2 = vcap2.read()

    return _calc_quality(metrics, total, cnt)


def _calc_metrics(frame1, frame2, metrics):
    return [m(frame1, frame2) for _, m in metrics]


def _calc_quality(metrics, total, cnt):
    return [(l, t / cnt) for (l, _), t in zip(metrics, total)]


def ber(path1, path2, wmtype, width=None):
    with create_reader(path1, wmtype, width=width) as wmreader1,\
            create_reader(path2, wmtype, width=width) as wmreader2:
        return _calculate_ber(wmreader1, wmreader2)


def _calculate_ber(wmreader1, wmreader2):
    errors = 0
    total = 0

    while wmreader1.available() and wmreader2.available():
        errors += (wmreader1.read_bit() != wmreader2.read_bit())
        total += 1

    return total, errors, (errors / total) if total else 1,
