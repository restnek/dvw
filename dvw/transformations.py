from abc import ABC, abstractmethod

import cv2
import numpy as np
from pywt import wavedec2, waverec2

from .util import get


class Transformation(ABC):
    @abstractmethod
    def transform(self, domain, memory=None):
        pass

    @abstractmethod
    def restore(self, domain, memory=None):
        pass


class UnionWithMemory(Transformation):
    def __init__(self, *transformations):
        self.memory = []
        self.transformations = transformations

    def transform(self, domain):
        for t in self.transformations:
            domain = t.transform(domain, self.memory)
        return domain

    def restore(self, domain):
        for t in reversed(self.transformations):
            domain = t.restore(domain, self.memory)
        return domain


class ChannelFilter(Transformation):
    def __init__(self, index):
        self.index = index

    def transform(self, domain, memory):
        domain = np.array(domain, copy=False)
        memory.append(domain)
        return domain[:, :, self.index]

    def restore(self, channel, memory):
        domain = memory.pop()
        domain[:, :, self.index] = channel
        return domain


class ItemFilter(Transformation):
    def __init__(self, index):
        self.index = index

    def transform(self, domain, memory):
        memory.append(domain)
        return domain[self.index]

    def restore(self, item, memory):
        domain = memory.pop()
        domain[self.index] = item
        return domain


class Normalize(Transformation):
    def __init__(self, factor):
        self.factor = factor

    def transform(self, domain, memory):
        return np.divide(domain, self.factor)

    def restore(self, domain, memory):
        return np.multiply(domain, self.factor)


class ToColorSpace(Transformation):
    def __init__(self, color_code, inverse_color_code):
        self.color_code = color_code
        self.inverse_color_code = inverse_color_code

    def transform(self, color, memory):
        return cv2.cvtColor(color, self.color_code)

    def restore(self, color, memory):
        return cv2.cvtColor(color, self.inverse_color_code)


class ToWavelet(Transformation):
    def __init__(self, wavelet='haar', level=1):
        self.wavelet = wavelet
        self.level = level

    def transform(self, domain, memory):
        return wavedec2(domain, self.wavelet, level=self.level)

    def restore(self, coeffs, memory):
        return waverec2(coeffs, self.wavelet)


def frame2wavelet(wavelet='haar', level=1):
    return UnionWithMemory(
        ToColorSpace(cv2.COLOR_BGR2YCrCb, cv2.COLOR_YCrCb2BGR),
        ChannelFilter(0),
        Normalize(255),
        ToWavelet(get(wavelet, 'haar'), get(level, 1)),
        ItemFilter(0))
