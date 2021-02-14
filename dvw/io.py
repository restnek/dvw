from abc import ABC, abstractmethod

import cv2

from . import media
from .util import bit2sign


class WatermarkReader(ABC):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def available(self):
        pass

    @abstractmethod
    def read_bit(self, sign=False):
        pass


class WatermarkWriter(ABC):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.flush()
        self.close()

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def flush(self):
        pass

    @abstractmethod
    def write_bit(self, bit):
        pass


class FileReader(WatermarkReader):
    def __init__(self, path, buffering=4096):
        self.file = open(path, 'rb', buffering)
        self.buffer = 0
        self.eof = False
        self.current = 256

    def close(self):
        self.file.close()

    def available(self):
        self.update()
        return not self.eof

    def read_bit(self, sign=False):
        self.update()

        bit = self.buffer & 1
        self.buffer >>= 1
        self.current += 1

        return bit2sign(bit) if sign else bit

    def update(self):
        if self.current > 7:
            byte_ = self.file.read(1)
            self.buffer = int.from_bytes(byte_, 'big')
            self.eof = (len(byte_) == 0)
            self.current = 0


class FileWriter(WatermarkWriter):
    def __init__(self, path, buffering=4096):
        self.file = open(path, 'wb', buffering)
        self.buffer = 0
        self.current = 0

    def close(self):
        self.file.close()

    def flush(self):
        self.file.flush()

    def write_bit(self, bit):
        self.buffer |= (bit << self.current)
        self.current += 1
        self.update()

    def update(self):
        if self.current > 7:
            self.file.write(self.buffer.to_bytes(1, 'big'))
            self.buffer = 0
            self.current = 0


class BWImageReader(WatermarkReader):
    def __init__(self, path, width=None):
        self.buffer = self._open(path, width)
        self.current = 0

    def _open(self, path, width):
        image = cv2.imread(path)
        if width:
            image = media.resize(image, width)
        return media.image2bin(image)

    def close(self):
        self.buffer = []

    def available(self):
        return self.current < len(self.buffer)

    def read_bit(self, sign=False):
        bit = self.buffer[self.current]
        self.current += 1
        return bit2sign(bit) if sign else bit


class BWImageWriter(WatermarkWriter):
    def __init__(self, path, width):
        self.path = path
        self.width = width
        self.buffer = []

    def close(self):
        self.buffer = []

    def flush(self):
        bw = media.bin2bw(self.buffer, self.width)
        cv2.imwrite(self.path, bw)

    def write_bit(self, bit):
        self.buffer.append(bit)


def create_reader(path, type_, **kwargs):
    reader, _ = _TYPES.get(type_, 'file')
    return reader(path, kwargs)


def create_writer(path, type_, **kwargs):
    _, writer = _TYPES.get(type_, 'file')
    return writer(path, kwargs)


def types():
    return dict.keys(_TYPES)


_TYPES = {
    'file': (
        lambda f, a=None: FileReader(f),
        lambda f, a=None: FileWriter(f)
    ),
    'image': (
        lambda f, a: BWImageReader(f, a['width']),
        lambda f, a: BWImageWriter(f, a['width'])
    ),
}
