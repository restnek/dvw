import operator
from dataclasses import dataclass
from functools import reduce
from itertools import combinations, product
from typing import Dict, Any, Type, List, Optional

import cerberus
import numpy as np
import yaml
from cerberus import errors
from pywt import wavelist

from dvw import attacks
from dvw.attacks import FlipAxis, RotateAngle
from dvw.core import algorithms
from dvw.core.methods import Emphasis, WindowPosition
from dvw.core.transforms import WaveletSubband
from dvw.io.watermark import WatermarkType
from dvw.metrics.video import VideoMetric
from dvw.metrics.watermark import WatermarkComparator, WatermarkMetric
from dvw.util import isstr, isarray, enum_values, isint, isdict, isnum, contains


class Validator(cerberus.Validator):
    def _validate_type_strings(self, x):
        return self.__validate_type_list_or_single(x, isstr)

    def _validate_type_integers(self, x):
        return self.__validate_type_list_or_single(
            x, isint
        ) or self.__validate_type_range(x, isint)

    def _validate_type_numbers(self, x):
        return self.__validate_type_list_or_single(
            x, isnum
        ) or self.__validate_type_range(x, isnum)

    def _validate_type_wavelets(self, x):
        return self.__validate_type_list_or_single(x, lambda v: v in wavelist())

    def _validate_type_dwtsub(self, x):  # check size
        if self.__validate_enums(x, WaveletSubband):
            return True
        elif not isdict(x) or len(x) != 3:
            return False
        elif not contains(x, "values", "min-length", "max-length"):
            return False
        elif not self.__validate_enums(x["values"], WaveletSubband):
            return False
        return True

    def _validate_type_winpos(self, x):
        return self.__validate_enums(x, WindowPosition)

    def _validate_type_emphasis(self, x):
        return self.__validate_enums(x, Emphasis)

    def _validate_type_vidmetric(self, x):
        return self.__validate_enums(x, VideoMetric)

    def _validate_type_wmmetric(self, x):
        return self.__validate_enums(x, WatermarkMetric)

    def _validate_type_flipaxis(self, x):
        return self.__validate_enums(x, FlipAxis)

    def _validate_type_rotang(self, x):
        return self.__validate_enums(x, RotateAngle)

    def _validate_min(self, min_value, field, value):
        """{'nullable': False }"""
        try:
            if isarray(value) and any(v < min_value for v in value):
                self._error(field, errors.MIN_VALUE)
            elif self.__validate_type_range(value):
                start, stop, step = value["start"], value["stop"], value.get("step", 1)
                if (start < min_value) if step > 0 else (stop + 1 < min_value):
                    self._error(field, errors.MIN_VALUE)
            elif value < min_value:
                self._error(field, errors.MIN_VALUE)
        except TypeError:
            pass

    def _validate_max(self, max_value, field, value):
        """{'nullable': False }"""
        try:
            if isarray(value) and any(v > max_value for v in value):
                self._error(field, errors.MAX_VALUE)
            elif self.__validate_type_range(value):
                start, stop, step = value["start"], value["stop"], value.get("step", 1)
                if (stop - 1 > max_value) if step > 0 else (start > max_value):
                    self._error(field, errors.MAX_VALUE)
            elif value > max_value:
                self._error(field, errors.MAX_VALUE)
        except TypeError:
            pass

    def __validate_type_list_or_single(self, x, test_fn):
        if test_fn(x):
            return True
        elif isarray(x):
            return all(map(test_fn, x))
        return False

    def __validate_type_range(self, x, test_fn=None):  # check size
        if not isdict(x) or len(x) > 3:
            return False
        elif not contains(x, "start", "stop"):
            return False
        elif len(x) == 3 and "step" not in x:
            return False
        elif test_fn and not all(map(test_fn, x.values())):
            return False
        return True

    def __validate_enums(self, x, enum):
        values = enum_values(enum)
        if isarray(x):
            return contains(values, *x)
        return x in values

    def _normalize_coerce_asrange(self, x):
        if isdict(x) and contains(x, "start", "stop"):
            return np.arange(**x)
        return self._normalize_coerce_aslist(x)

    def _normalize_coerce_dwtsub(self, x):
        if isdict(x) and contains(x, "values", "min-length", "max-length"):
            combs = []
            values, min_len, max_len = x["values"], x["min-length"], x["max-length"]
            values = list(map(WaveletSubband, values))
            for i in range(min_len, max_len + 1):
                combs.extend(combinations(values, i))
            return combs
        values = self._normalize_coerce_aslist(x)
        return [[WaveletSubband(x) for x in v] for v in values]

    def _normalize_coerce_winpos(self, x):
        return self._normalize_coerce_aslist(x, WindowPosition)

    def _normalize_coerce_emphasis(self, x):
        return self._normalize_coerce_aslist(x, Emphasis)

    def _normalize_coerce_vidmetric(self, x):
        return self._normalize_coerce_aslist(x, VideoMetric)

    def _normalize_coerce_wmmetric(self, x):
        return self._normalize_coerce_aslist(x, WatermarkMetric)

    def _normalize_coerce_flipaxis(self, x):
        return self._normalize_coerce_aslist(x, FlipAxis)

    def _normalize_coerce_rotang(self, x):
        return self._normalize_coerce_aslist(x, RotateAngle)

    def _normalize_coerce_aslist(self, x, type_=None):
        if not isarray(x):
            x = [x]
        if type_:
            x = list(map(type_, x))
        return x


@dataclass
class WatermarkHolder:
    type: WatermarkType
    path: str
    params: Optional[Dict[str, Any]] = None

    def reader(self):
        return self.type.reader(self.path, **self.params)

    def writer(self, path):
        return self.type.writer(path, **self.params)

    def compare(self, path, precision, metrics):
        comparator = WatermarkComparator(precision, *metrics)
        return comparator.compare(self.path, path, self.type, **self.params)

    @staticmethod
    def from_dict(data):
        watermarks = []
        for k, v in data.items():
            type_ = WatermarkType(k)
            for x in v:
                if isdict(x):
                    path = x.pop("path")
                    holder = WatermarkHolder(type_, path, x)
                    watermarks.append(holder)
                elif isstr(x):
                    watermarks.append(WatermarkHolder(type_, x))
        return watermarks


@dataclass
class ClassHolder:
    class_: Type
    params: Dict[str, list]

    @property
    def total(self) -> int:
        return reduce(operator.mul, map(len, self.params.values()))

    def __iter__(self):
        keys = self.params.keys()
        values = self.params.values()
        for v in product(*values):
            params = dict(zip(keys, v))
            yield self.class_(**params), params

    @staticmethod
    def from_dict(data, name2class):
        return [ClassHolder(name2class(k), v) for k, v in data.items()]


@dataclass
class AnalysisKit:
    algorithms: List[ClassHolder]
    videos: List[str]
    watermarks: List[WatermarkHolder]
    attacks: List[ClassHolder]
    video_metrics: List[VideoMetric]
    watermark_metrics: List[WatermarkMetric]

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AnalysisKit":
        videos = data["videos"]
        watermarks = WatermarkHolder.from_dict(data["watermarks"])

        algorithms_ = ClassHolder.from_dict(data["algorithms"], algorithms.name2class)
        attacks_ = None
        if "attacks" in data:
            attacks_ = ClassHolder.from_dict(data["attacks"], attacks.name2class)

        video_metrics = None
        watermark_metrics = None
        if "metrics" in data:
            video_metrics = data["metrics"].get("video")
            watermark_metrics = data["metrics"].get("watermark")

        return AnalysisKit(
            algorithms_, videos, watermarks, attacks_, video_metrics, watermark_metrics
        )


def config2kit(path: str) -> AnalysisKit:
    with open(path) as config_file:
        config = yaml.safe_load(config_file)

        validator = Validator(_SCHEMA)
        valid = validator.validate(config, normalize=False)
        config = validator.normalized(config)

        return AnalysisKit.from_dict(config)


def integers(**kwargs):
    type_ = {"coerce": "asrange", "type": "integers"}
    type_.update(kwargs)
    return type_


def numbers(**kwargs):
    type_ = {"coerce": "asrange", "type": "numbers"}
    type_.update(kwargs)
    return type_


def aslist(type_):
    return {"coerce": "aslist", "type": type_}


def asenum(type_):
    return {"coerce": type_, "type": type_}


_SCHEMA = {
    "videos": aslist("strings"),
    "watermarks": {
        "type": "dict",
        "schema": {
            "bit-file": aslist("strings"),
            "bw-image": {
                "coerce": "aslist",
                "type": ["strings", "dict"],
                "schema": {
                    "path": {"required": True, "type": "string"},
                    "width": {"type": "integer"},
                },
            },
        },
    },
    "algorithms": {
        "type": "dict",
        "schema": {
            "dwt-window-median": {
                "type": "dict",
                "schema": {
                    "wavelet": aslist("wavelets"),
                    "level": integers(min=1),
                    "subbands": asenum("dwtsub"),
                    "position": asenum("winpos"),
                    "window-size": integers(min=3, rename="window_size"),
                    "emphasis": asenum("emphasis"),
                },
            },
            "dwt-dct-even-odd-differential": {
                "type": "dict",
                "schema": {
                    "wavelet": aslist("wavelets"),
                    "level": integers(min=1),
                    "subbands": asenum("dwtsub"),
                    "offset": numbers(min=0, max=1),
                    "area": numbers(min=0, max=1),
                    "alpha": numbers(min=0),
                    "repeats": integers(min=1),
                    "emphasis": asenum("emphasis"),
                },
            },
            "dwt-svd-mean-over-window-edges": {
                "type": "dict",
                "schema": {
                    "wavelet": aslist("wavelets"),
                    "level": integers(min=1),
                    "subbands": asenum("dwtsub"),
                    "window-size": integers(min=3, rename="window_size"),
                    "alpha": numbers(min=0),
                    "emphasis": asenum("emphasis"),
                },
            },
        },
    },
    "metrics": {
        "type": "dict",
        "required": False,
        "schema": {"video": asenum("vidmetric"), "watermark": asenum("wmmetric")},
    },
    "attacks": {
        "type": "dict",
        "required": False,
        "schema": {
            "flip": {"type": "dict", "schema": {"axis": asenum("flipaxis")}},
            "resize": {
                "type": "dict",
                "schema": {"height": integers(min=0), "width": integers(min=0)},
            },
            "crop": {
                "type": "dict",
                "schema": {
                    "y": integers(min=0),
                    "x": integers(min=0),
                    "height": integers(min=0),
                    "width": integers(min=0),
                },
            },
            "fill": {
                "type": "dict",
                "schema": {
                    "y": integers(min=0),
                    "x": integers(min=0),
                    "height": integers(min=0),
                    "width": integers(min=0),
                    "value": integers(min=0, max=255),
                },
            },
            "rotate": {"type": "dict", "schema": {"angle": numbers(min=0)}},
            "gaussian": {
                "type": "dict",
                "schema": {"std": numbers(min=0), "area": numbers(min=0, max=1)},
            },
            "salt-and-pepper": {
                "type": "dict",
                "schema": {"area": numbers(min=0, max=1)},
            },
        },
    },
}
