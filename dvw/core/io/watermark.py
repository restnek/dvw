from abc import ABC, abstractmethod
from enum import Enum
from random import Random

import cv2
import numpy as np

from ..util.base import AutoCloseable


class WatermarkBitReader(AutoCloseable, ABC):
    @abstractmethod
    def available(self):
        pass

    @abstractmethod
    def read_bit(self):
        pass


class WatermarkBitBatchReader(AutoCloseable, ABC):
    @abstractmethod
    def read_all(self):
        pass


class WatermarkBitGenerator(WatermarkBitReader, ABC):
    def __init__(self, size=None):
        self.size = size

    def close(self):
        pass

    def available(self):
        return (self.size is None) or (self.size > 0)

    def _reduce_size(self):
        if self.size and self.size > 0:
            self.size -= 1


class WatermarkBitWriter(AutoCloseable, ABC):
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()
        self.close()

    @abstractmethod
    def flush(self):
        pass

    @abstractmethod
    def write_bit(self, bit):
        pass


class ConstantBitReader(WatermarkBitGenerator):
    def __init__(self, bit, size=None):
        super().__init__(size)
        self.bit = int(bool(bit))

    def read_bit(self):
        self._reduce_size()
        return self.bit


class RandomBitReader(WatermarkBitGenerator):
    def __init__(self, seed, size=None):
        super().__init__(size)
        self.generator = Random(seed)

    def read_bit(self):
        self._reduce_size()
        return self.generator.getrandbits(1)


class BitFileReader(WatermarkBitReader, WatermarkBitBatchReader):
    def __init__(self, path, buffering=4096):
        self.file = open(path, 'rb', buffering)
        self.buffer = 0
        self.eof = False
        self.current = 256

    def close(self):
        self.file.close()

    def available(self):
        self._update()
        return not self.eof

    def read_bit(self):
        self._update()

        bit = self.buffer & 1
        self.buffer >>= 1
        self.current += 1

        return bit

    def _update(self):
        if self.current > 7:
            byte_ = self.file.read(1)
            self.buffer = int.from_bytes(byte_, 'big')
            self.eof = (len(byte_) == 0)
            self.current = 0

    def read_all(self):
        self.eof = True
        return self.file.read()


class BitFileWriter(WatermarkBitWriter):
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
        self._update()

    def _update(self):
        if self.current > 7:
            self.file.write(self.buffer.to_bytes(1, 'big'))
            self.buffer = 0
            self.current = 0


class BWImageReader(WatermarkBitReader, WatermarkBitBatchReader):
    def __init__(self, path, width=None):
        self.buffer = self._open(path, width)
        self.width = width
        self.current = 0

    def _open(self, path, width):
        image = cv2.imread(path)
        return self._image2bin(image, width)

    def _image2bin(self, image, width):
        if width:
            image = self._resize(image, width)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, bw = cv2.threshold(gray, 127, 1, cv2.THRESH_BINARY)
        return bw.reshape(-1)

    def _resize(self, image, width):
        shape = np.shape(image)
        height = int(shape[0] * width / shape[1])
        return cv2.resize(image, (width, height))

    def close(self):
        self.buffer = []

    def available(self):
        return self.current < len(self.buffer)

    def read_bit(self):
        bit = self.buffer[self.current]
        self.current += 1
        return bit

    def read_all(self):
        self.current = len(self.buffer)
        return self.buffer


class BWImageWriter(WatermarkBitWriter):
    def __init__(self, path, width):
        self.path = path
        self.width = width
        self.buffer = []

    def close(self):
        self.buffer = []

    def flush(self):
        bw = self._buffer2bw()
        cv2.imwrite(self.path, bw)

    def _buffer2bw(self):
        bw = [(255 if b else 0) for b in self.buffer]
        return np.reshape(bw, (-1, self.width))

    def write_bit(self, bit):
        self.buffer.append(bit)


class WatermarkType(Enum):
    BIT_FILE = (
        'bit-file',
        lambda f, **a: BitFileReader(f),
        lambda f, **a: BitFileWriter(f))
    BW_IMAGE = (
        'bw-image',
        lambda f, **a: BWImageReader(f, a['width']),
        lambda f, **a: BWImageWriter(f, a['width']))

    def __new__(cls, value, reader_class, writer_class):
        obj = object().__new__(cls)
        obj._value_ = value
        obj.reader = reader_class
        obj.writer = writer_class
        return obj
