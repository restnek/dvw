from abc import ABC, abstractmethod

from .util import middle


class Method(ABC):
    @abstractmethod
    def embed(self, domain, wmreader):
        pass

    @abstractmethod
    def extract(self, wmdomain, wmwriter, quantity, domain=None):
        pass


class WindowMedian(Method):
    def embed(self, domain, wmreader):
        embedded = 0
        for r in domain:
            for i in range(0, len(r) - 2, 3):
                if not wmreader.available():
                    return domain, embedded
                r[i:i+3] = self._embed_bit(r[i:i+3], wmreader.read_bit())
                embedded += 1
        return domain, embedded

    def _embed_bit(self, window, bit):
        _, i = middle(*window)
        mn, mx = min(window), max(window)
        window[i] = mx if bit else mn
        return window

    def extract(self, wmdomain, wmwriter, quantity):
        extracted = 0
        for r in wmdomain:
            for i in range(0, len(r) - 2, 3):
                if quantity < 1:
                    return extracted
                self._extract_bit(r[i:i+3], wmwriter)
                extracted += 1
                quantity -= 1
        return extracted

    def _extract_bit(self, window, wmwriter):
        mid, _ = middle(*window)
        mn, mx = min(window), max(window)
        wmwriter.write_bit(int(mid >= (mx + mn) / 2))
