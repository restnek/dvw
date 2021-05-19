from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Tuple

import numpy as np

from dvw.io.watermark import WatermarkBitReader, WatermarkBitWriter
from dvw.util import bit2sign


class Method(ABC):
    @abstractmethod
    def embed(
        self, domain: np.ndarray, watermark_reader: WatermarkBitReader
    ) -> Tuple[np.ndarray, int]:
        pass

    @abstractmethod
    def extract(
        self,
        domain: np.ndarray,
        watermark_writer: WatermarkBitWriter,
        quantity: int,
    ) -> int:
        pass


class BitManipulator(ABC):
    @abstractmethod
    def embed(self, domain: np.ndarray, bit: int) -> np.ndarray:
        pass

    @abstractmethod
    def extract(self, domain: np.ndarray) -> int:
        pass


class WindowPosition(Enum):
    HORIZONTAL = "hr"
    VERTICAL = "vr"


class WindowMedian(Method):
    def __init__(self, window_size: int, submethod: Method) -> None:
        self.window_size = window_size
        self.submethod = submethod

    def embed(
        self, domain: np.ndarray, watermark_reader: WatermarkBitReader
    ) -> Tuple[np.ndarray, int]:
        embedded = 0
        domain = np.asarray(domain)

        for r in domain:
            for j in range(0, len(r) - (self.window_size - 1), self.window_size):
                if not watermark_reader.available():
                    return domain, embedded
                window = r[j : j + self.window_size].T
                window, amount = self.submethod.embed(window, watermark_reader)
                embedded += amount

        return domain, embedded

    def extract(
        self, domain: np.ndarray, watermark_writer: WatermarkBitWriter, quantity: int
    ) -> int:
        extracted = 0

        for r in domain:
            for j in range(0, len(r) - (self.window_size - 1), self.window_size):
                if quantity < 1:
                    return extracted
                window = np.transpose(r[j : j + self.window_size])
                amount = self.submethod.extract(window, watermark_writer, quantity)
                extracted += amount
                quantity -= amount

        return extracted


class WindowMedianBitManipulator(BitManipulator):
    def embed(self, window: np.ndarray, bit: int) -> np.ndarray:
        imin, imax = window.argmin(), window.argmax()

        for i in range(len(window)):
            if i != imin and i != imax:
                window[i] = window[imax] if bit else window[imin]

        return window

    def extract(self, window: np.ndarray) -> int:
        cnt = 0
        imin, imax = window.argmin(), window.argmax()

        for i, x in enumerate(window):
            if i != imin and i != imax:
                mid = (window[imin] + window[imax]) / 2
                cnt += bit2sign(x >= mid)

        return int(cnt >= 0)


class EvenOddDifferential(Method):
    def __init__(
        self, offset: float, area: float, repeats: int, submethod: Method
    ) -> None:
        self.offset = offset
        self.area = area
        self.repeats = repeats
        self.submethod = submethod

    def embed(
        self, domain: np.ndarray, watermark_reader: WatermarkBitReader
    ) -> Tuple[np.ndarray, int]:
        embedded = 0
        domain = np.asarray(domain)
        start, end = self._find_boundaries(domain[0])

        for i in range(start, end - (self.repeats - 1), self.repeats):
            if not watermark_reader.available():
                break
            windows = domain[:, :, i : i + self.repeats]
            windows, amount = self.submethod.embed(windows, watermark_reader)
            embedded += amount

        return domain, embedded

    def extract(
        self, domain: np.ndarray, watermark_writer: WatermarkBitWriter, quantity: int
    ) -> int:
        extracted = 0
        domain = np.asarray(domain)
        start, end = self._find_boundaries(domain[0])

        for i in range(start, end - (self.repeats - 1), self.repeats):
            if quantity < 1:
                break
            windows = domain[:, :, i : i + self.repeats]
            amount = self.submethod.extract(windows, watermark_writer, quantity)
            extracted += amount
            quantity -= amount

        return extracted

    def _find_boundaries(self, domain: np.ndarray) -> Tuple[int, int]:
        even, odd = domain
        size = min(len(even), len(odd))
        start = int(self.offset * size)
        end = min(start + int(self.area * size), size)
        return start, end


class EvenOddDifferentialBitManipulator(BitManipulator):
    def __init__(self, alpha: float) -> None:
        self.alpha = alpha

    def embed(self, domain: np.ndarray, bit: int) -> np.ndarray:
        even, odd = domain
        bit = bit2sign(bit)

        for i in range(len(even)):
            avg = 0.5 * (even[i] + odd[i])
            even[i] = avg + bit * self.alpha
            odd[i] = avg - bit * self.alpha

        return domain

    def extract(self, domain: np.ndarray) -> int:
        cnt = 0
        even, odd = domain

        for e, o in zip(even, odd):
            cnt += bit2sign((e - o) >= 0)

        return int(cnt >= 0)


class MeanOverWindowEdges(Method):
    def __init__(self, window_size: int, submethod: Method) -> None:
        self.window_size = window_size
        self.submethod = submethod

    def embed(
        self, domain: np.ndarray, watermark_reader: WatermarkBitReader
    ) -> Tuple[np.ndarray, int]:
        embedded = 0
        domain = np.asarray(domain)

        for i in range(0, domain.shape[1] - (self.window_size - 1), self.window_size):
            if not watermark_reader.available():
                break
            windows = domain[:, i : i + self.window_size]
            windows, amount = self.submethod.embed(windows, watermark_reader)
            embedded += amount

        return domain, embedded

    def extract(
        self, domain: np.ndarray, watermark_writer: WatermarkBitWriter, quantity: int
    ) -> int:
        extracted = 0
        domain = np.asarray(domain)

        for i in range(0, domain.shape[1] - (self.window_size - 1), self.window_size):
            if quantity < 1:
                break
            windows = domain[:, i : i + self.window_size]
            amount = self.submethod.extract(windows, watermark_writer, quantity)
            extracted += amount
            quantity -= amount

        return extracted


class MeanOverWindowEdgesBitManipulator(BitManipulator):
    def __init__(self, alpha: float) -> None:
        self.alpha = alpha

    def embed(self, window: np.ndarray, bit: int) -> np.ndarray:
        bit = bit2sign(bit)
        sm = window[0] + window[-1]
        window[1:-1] = 0.5 * (sm + bit * self.alpha * sm)
        return window

    def extract(self, window: np.ndarray) -> int:
        cnt = 0
        avg = 0.5 * (window[0] + window[-1])

        for i in range(1, len(window)):
            cnt += bit2sign(window[i] > avg)

        return int(cnt >= 0)


class RobustnessEmphasis(Method):
    def __init__(self, bit_manipulator: BitManipulator) -> None:
        self.bit_manipulator = bit_manipulator

    def embed(
        self, domains: np.ndarray, watermark_reader: WatermarkBitReader
    ) -> Tuple[np.ndarray, int]:
        bit = watermark_reader.read_bit()

        for d in domains:
            self.bit_manipulator.embed(d, bit)

        return domains, 1

    def extract(
        self, domains: np.ndarray, watermark_writer: WatermarkBitWriter, quantity: int
    ) -> int:
        cnt = 0

        for d in domains:
            cnt += self.bit_manipulator.extract(d)

        bit = int(cnt > len(domains) // 2)
        watermark_writer.write_bit(bit)

        return 1


class CapacityEmphasis(Method):
    def __init__(self, bit_manipulator: BitManipulator) -> None:
        self.bit_manipulator = bit_manipulator

    def embed(
        self, domains: np.ndarray, watermark_reader: WatermarkBitReader
    ) -> Tuple[np.ndarray, int]:
        embedded = 0

        for d in domains:
            if not watermark_reader.available():
                break
            bit = watermark_reader.read_bit()
            self.bit_manipulator.embed(d, bit)
            embedded += 1

        return domains, embedded

    def extract(
        self, domains: np.ndarray, watermark_writer: WatermarkBitWriter, quantity: int
    ) -> int:
        extracted = 0

        for d in domains:
            if quantity < 1:
                break
            bit = self.bit_manipulator.extract(d)
            watermark_writer.write_bit(bit)
            extracted += 1
            quantity -= 1

        return extracted


class Emphasis(Enum):
    ROBUSTNESS = ("robustness", RobustnessEmphasis)
    CAPACITY = ("capacity", CapacityEmphasis)

    def __new__(
        cls, value: str, class_: Callable[[BitManipulator], Method]
    ) -> "Emphasis":
        obj = object().__new__(cls)
        obj._value_ = value
        obj.create = class_
        return obj
