from abc import ABC, abstractmethod
from enum import Enum
from typing import List

import cv2
import numpy as np
from pywt import waverec2, wavedec2

from dvw.core.methods import WindowPosition
from dvw.core.util.util import tuple2list


class Transformation(ABC):
    @abstractmethod
    def transform(self, domain, memory: list):
        pass

    @abstractmethod
    def restore(self, domain, memory: list):
        pass


class WaveletSubband(Enum):
    LL = ("LL", 0)
    LH = ("LH", 1)
    HL = ("HL", 2)
    HH = ("HH", 3)

    def __new__(cls, value: str, index: int) -> "WaveletSubband":
        obj = object().__new__(cls)
        obj._value_ = value
        obj.index = index
        return obj


class Pipe(Transformation):
    def __init__(self, *transformations: Transformation) -> None:
        self.transformations = list(transformations)

    def extend(self, *transformations: Transformation) -> None:
        self.transformations.extend(transformations)

    def transform(self, domain, memory: list):
        for t in self.transformations:
            domain = t.transform(domain, memory)
        return domain

    def restore(self, domain, memory: list):
        for t in reversed(self.transformations):
            domain = t.restore(domain, memory)
        return domain


class Every(Pipe):
    def transform(self, domains, memory: list):
        return [super(Every, self).transform(d, memory) for d in domains]

    def restore(self, domains, memory: list):
        domains = [super(Every, self).restore(d, memory) for d in reversed(domains)]
        return domains[::-1]


class ChannelFilter(Transformation):
    def __init__(self, index: int) -> None:
        self.index = index

    def transform(self, domain, memory: list) -> np.ndarray:
        domain = np.asarray(domain)
        memory.append(domain)
        return domain[:, :, self.index]

    def restore(self, channel: np.ndarray, memory: list) -> np.ndarray:
        domain = memory.pop()
        domain[:, :, self.index] = channel
        return domain


class ItemFilter(Transformation):
    def __init__(self, index: int) -> None:
        self.index = index

    def transform(self, domain, memory: list):
        domain = tuple2list(domain)
        memory.append(domain)
        return domain[self.index]

    def restore(self, item, memory: list):
        domain = memory.pop()
        domain[self.index] = item
        return domain


class WaveletFilter(Transformation):
    def __init__(self, *subbands: WaveletSubband):
        self.indices = sorted(s.index for s in set(subbands))

    def transform(self, domain, memory: list):
        domain = tuple2list(domain)
        memory.append(domain)
        return [domain[i] for i in self.indices]

    def restore(self, subbands, memory: list):
        domain = memory.pop()
        for i, k in enumerate(self.indices):
            domain[k] = subbands[i]
        return domain


class Reshape(Transformation):
    def __init__(self, shape) -> None:
        self.shape = shape

    def transform(self, domain, memory: list) -> np.ndarray:
        memory.append(np.shape(domain))
        return np.reshape(domain, self.shape)

    def restore(self, domain: np.ndarray, memory: list) -> np.ndarray:
        shape = memory.pop()
        return np.reshape(domain, shape)


class Transpose(Transformation):
    def transform(self, domain, memory: list) -> np.ndarray:
        return np.asarray(domain).T

    def restore(self, domain: np.ndarray, memory: list) -> np.ndarray:
        return np.asarray(domain).T


class DepthStack(Transformation):
    def transform(self, domain, memory: list) -> np.ndarray:
        return np.dstack(domain)

    def restore(self, domain: np.ndarray, memory: list) -> List[np.ndarray]:
        depth = np.shape(domain)[2]
        return [domain[:, :, i] for i in range(depth)]


class Normalize(Transformation):
    def __init__(self, factor: float) -> None:
        self.factor = factor

    def transform(self, domain, memory: list) -> np.ndarray:
        return np.divide(domain, self.factor)

    def restore(self, domain: np.ndarray, memory: list) -> np.ndarray:
        return np.multiply(domain, self.factor)


class ToZigzagOrder(Transformation):
    def transform(self, domain, memory: list) -> np.ndarray:
        shape = np.shape(domain)[:2]
        memory.append(shape)
        return np.asarray([domain[i][j] for i, j in self._zigzag_indices(*shape)])

    def restore(self, array: np.ndarray, memory: list) -> np.ndarray:
        rows, columns = memory.pop()
        domain = [[0 for _ in range(columns)] for _ in range(rows)]
        for k, (i, j) in enumerate(self._zigzag_indices(rows, columns)):
            domain[i][j] = array[k]
        return np.asarray(domain)

    def _zigzag_indices(self, rows: int, columns: int) -> np.ndarray:
        indices = [[] for _ in range(rows + columns - 1)]

        for i in range(rows):
            for j in range(columns):
                sm = i + j
                if sm % 2 == 0:
                    indices[sm].insert(0, (i, j))
                else:
                    indices[sm].append((i, j))

        return np.concatenate(indices)


class EvenOddDecomposition(Transformation):
    def transform(self, domain, memory: list):
        return domain[::2], domain[1::2]

    def restore(self, domain, memory: list) -> np.ndarray:
        return np.vstack((domain[0], domain[1])).ravel(order="F")


class SingularValueDecomposition(Transformation):
    def transform(self, domain, memory: list):
        return np.linalg.svd(domain, full_matrices=False)

    def restore(self, domain, memory: list):
        u, s, vh = map(np.asarray, domain)
        return (u * s) @ vh


class ToColorSpace(Transformation):
    def __init__(self, color_code: int, inverse_color_code: int) -> None:
        self.color_code = color_code
        self.inverse_color_code = inverse_color_code

    def transform(self, color, memory: list) -> np.ndarray:
        return cv2.cvtColor(color, self.color_code)

    def restore(self, color, memory: list) -> np.ndarray:
        return cv2.cvtColor(color, self.inverse_color_code)


class ToCosineTransform(Transformation):
    def transform(self, domain, memory: list):
        domain = np.asarray(domain)
        memory.append(domain.shape)
        return cv2.dct(domain)

    def restore(self, domain, memory: list):
        shape = memory.pop()
        domain = cv2.idct(domain)
        return domain.reshape(shape)


class ToWavelet(Transformation):
    def __init__(self, wavelet: str, level: int) -> None:
        self.wavelet = wavelet
        self.level = level

    def transform(self, domain, memory: list):
        coeffs = wavedec2(domain, self.wavelet, level=self.level)
        memory.append(coeffs)
        return (coeffs[0], *coeffs[1])

    def restore(self, subbands, memory: list) -> np.ndarray:
        coeffs = memory.pop()
        coeffs[0] = subbands[0]
        coeffs[1] = subbands[1:]
        return waverec2(coeffs, self.wavelet)


def frame2wavelet(wavelet: str, level: int, *subbands: WaveletSubband) -> Pipe:
    return Pipe(
        ToColorSpace(cv2.COLOR_BGR2YCrCb, cv2.COLOR_YCrCb2BGR),
        ChannelFilter(0),
        Normalize(255),
        ToWavelet(wavelet, level),
        WaveletFilter(*subbands),
    )


def frame2dwt_stack(
    wavelet: str, level: int, position: WindowPosition, *subbands: WaveletSubband
) -> Pipe:
    pipe = frame2wavelet(wavelet, level, *subbands)
    if WindowPosition.VERTICAL == position:
        pipe.extend(Every(Transpose()))
    pipe.extend(DepthStack())
    return pipe


def frame2dwt_dct(wavelet: str, level: int, *subbands: WaveletSubband) -> Pipe:
    return Pipe(
        frame2wavelet(wavelet, level, *subbands),
        Every(
            ToZigzagOrder(),
            EvenOddDecomposition(),
            Every(ToCosineTransform(), Reshape(-1)),
        ),
    )


def frame2dwt_svd(wavelet, level, *subbands):
    return Pipe(
        frame2wavelet(wavelet, level, *subbands),
        Every(SingularValueDecomposition(), ItemFilter(1)),
    )
