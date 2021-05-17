from abc import ABC, abstractmethod
from enum import Enum

import cv2
import numpy as np
from pywt import waverec2, wavedec2

from dvw.core.methods import WindowPosition
from dvw.core.util.util import tuple2list


class Transformation(ABC):
    @abstractmethod
    def transform(self, domain, memory):
        pass

    @abstractmethod
    def restore(self, domain, memory):
        pass


class WaveletSubband(Enum):
    LL = ("LL", 0)
    LH = ("LH", 1)
    HL = ("HL", 2)
    HH = ("HH", 3)

    def __new__(cls, value, index):
        obj = object().__new__(cls)
        obj._value_ = value
        obj.index = index
        return obj


class Pipe(Transformation):
    def __init__(self, *transformations):
        self.transformations = list(transformations)

    def extend(self, *transformations):
        self.transformations.extend(transformations)

    def transform(self, domain, memory):
        for t in self.transformations:
            domain = t.transform(domain, memory)
        return domain

    def restore(self, domain, memory):
        for t in reversed(self.transformations):
            domain = t.restore(domain, memory)
        return domain


class Every(Pipe):
    def transform(self, domains, memory):
        return [super(Every, self).transform(d, memory) for d in domains]

    def restore(self, domains, memory):
        domains = [super(Every, self).restore(d, memory) for d in reversed(domains)]
        return domains[::-1]


class ChannelFilter(Transformation):
    def __init__(self, index: int):
        self.index = index

    def transform(self, domain, memory):
        domain = np.asarray(domain)
        memory.append(domain)
        return domain[:, :, self.index]

    def restore(self, channel, memory):
        domain = memory.pop()
        domain[:, :, self.index] = channel
        return domain


class ItemFilter(Transformation):
    def __init__(self, index: int):
        self.index = index

    def transform(self, domain, memory):
        domain = tuple2list(domain)
        memory.append(domain)
        return domain[self.index]

    def restore(self, item, memory):
        domain = memory.pop()
        domain[self.index] = item
        return domain


class WaveletFilter(Transformation):
    def __init__(self, *subbands):
        self.indices = sorted(s.index for s in set(subbands))

    def transform(self, domain, memory):
        domain = tuple2list(domain)
        memory.append(domain)
        return [domain[i] for i in self.indices]

    def restore(self, subbands, memory):
        domain = memory.pop()
        for i, k in enumerate(self.indices):
            domain[k] = subbands[i]
        return domain


class Reshape(Transformation):
    def __init__(self, shape):
        self.shape = shape

    def transform(self, domain, memory):
        memory.append(np.shape(domain))
        return np.reshape(domain, self.shape)

    def restore(self, domain, memory):
        shape = memory.pop()
        return np.reshape(domain, shape)


class Transpose(Transformation):
    def transform(self, domain, memory):
        return np.asarray(domain).T

    def restore(self, domain, memory):
        return np.asarray(domain).T


class DepthStack(Transformation):
    def transform(self, domain, memory):
        return np.dstack(domain)

    def restore(self, domain, memory):
        depth = np.shape(domain)[2]
        return [domain[:, :, i] for i in range(depth)]


class Normalize(Transformation):
    def __init__(self, factor):
        self.factor = factor

    def transform(self, domain, memory):
        return np.divide(domain, self.factor)

    def restore(self, domain, memory):
        return np.multiply(domain, self.factor)


class ToZigzagOrder(Transformation):
    def transform(self, domain, memory):
        shape = np.shape(domain)[:2]
        memory.append(shape)
        return [domain[i][j] for i, j in self._zigzag_indices(*shape)]

    def restore(self, array, memory):
        rows, columns = memory.pop()
        domain = [[0 for _ in range(columns)] for _ in range(rows)]
        for k, (i, j) in enumerate(self._zigzag_indices(rows, columns)):
            domain[i][j] = array[k]
        return np.asarray(domain)

    def _zigzag_indices(self, rows, columns):
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
    def transform(self, domain, memory):
        return domain[::2], domain[1::2]

    def restore(self, domain, memory):
        return np.vstack((domain[0], domain[1])).ravel(order="F")


class SingularValueDecomposition(Transformation):
    def transform(self, domain, memory):
        return np.linalg.svd(domain, full_matrices=False)

    def restore(self, domain, memory):
        u, s, vh = map(np.asarray, domain)
        return (u * s) @ vh


class ToColorSpace(Transformation):
    def __init__(self, color_code, inverse_color_code):
        self.color_code = color_code
        self.inverse_color_code = inverse_color_code

    def transform(self, color, memory):
        return cv2.cvtColor(color, self.color_code)

    def restore(self, color, memory):
        return cv2.cvtColor(color, self.inverse_color_code)


class ToCosineTransform(Transformation):
    def transform(self, domain, memory):
        domain = np.asarray(domain)
        memory.append(domain.shape)
        return cv2.dct(domain)

    def restore(self, domain, memory):
        shape = memory.pop()
        domain = cv2.idct(domain)
        return domain.reshape(shape)


class ToWavelet(Transformation):
    def __init__(self, wavelet, level):
        self.wavelet = wavelet
        self.level = level

    def transform(self, domain, memory):
        coeffs = wavedec2(domain, self.wavelet, level=self.level)
        memory.append(coeffs)
        return coeffs[0], *coeffs[1]

    def restore(self, subbands, memory):
        coeffs = memory.pop()
        coeffs[0] = subbands[0]
        coeffs[1] = subbands[1:]
        return waverec2(coeffs, self.wavelet)


def frame2wavelet(wavelet, level, *subbands):
    return Pipe(
        ToColorSpace(cv2.COLOR_BGR2YCrCb, cv2.COLOR_YCrCb2BGR),
        ChannelFilter(0),
        Normalize(255),
        ToWavelet(wavelet, level),
        WaveletFilter(*subbands))


def frame2dwt_stack(wavelet, level, position, *subbands):
    pipe = frame2wavelet(wavelet, level, *subbands)
    if WindowPosition.VERTICAL == position:
        pipe.extend(Every(Transpose()))
    pipe.extend(DepthStack())
    return pipe


def frame2dwt_dct(wavelet, level, *subbands):
    return Pipe(
        frame2wavelet(wavelet, level, *subbands),
        Every(
            ToZigzagOrder(),
            EvenOddDecomposition(),
            Every(
                ToCosineTransform(),
                Reshape(-1))))


def frame2dwt_svd(wavelet, level, *subbands):
    return Pipe(
        frame2wavelet(wavelet, level, *subbands),
        Every(
            SingularValueDecomposition(),
            ItemFilter(1)))
