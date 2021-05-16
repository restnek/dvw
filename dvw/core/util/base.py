from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import replace, dataclass


class AutoCloseable(ABC):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @abstractmethod
    def close(self):
        pass


@dataclass
class CloneableDataclass(ABC):
    def shallow_copy(self):
        return replace(self)


class Subscriber(ABC):
    @abstractmethod
    def update(self, event, **kwargs):
        pass


class Observable(ABC):
    def __init__(self):
        self.subscribers = defaultdict(set)

    def subscribe(self, subscriber, *events):
        for e in events:
            self.subscribers[e].add(subscriber)

    def unsubscribe(self, subscriber, *events):
        if events:
            self.unsubscribe_events(subscriber, events)
        else:
            self.unsubscribe_everywhere(subscriber)

    def unsubscribe_everywhere(self, subscriber):
        for s in self.subscribers.values():
            s.discard(subscriber)

    def unsubscribe_events(self, subscriber, events):
        for e in events:
            self.subscribers[e].discard(subscriber)

    def notify(self, event, **kwargs):
        for s in self.subscribers[event]:
            s.update(event, **kwargs)
