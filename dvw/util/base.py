from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import replace, dataclass
from types import TracebackType
from typing import Dict, Any, Optional, Type


class AutoCloseable(ABC):
    def __enter__(self) -> "AutoCloseable":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    @abstractmethod
    def close(self) -> None:
        pass


@dataclass
class CloneableDataclass(ABC):
    def shallow_copy(self) -> "CloneableDataclass":
        return replace(self)


class PrettyDictionary(ABC):
    @abstractmethod
    def dictionary(self) -> Dict[str, Any]:
        pass


class Subscriber(ABC):
    @abstractmethod
    def update(self, event, **kwargs) -> None:
        pass


class Observable(ABC):
    def __init__(self) -> None:
        self.subscribers = defaultdict(set)

    def subscribe(self, subscriber: Subscriber, *events) -> None:
        for e in events:
            self.subscribers[e].add(subscriber)

    def unsubscribe(self, subscriber: Subscriber, *events) -> None:
        if events:
            self.unsubscribe_events(subscriber, events)
        else:
            self.unsubscribe_everywhere(subscriber)

    def unsubscribe_everywhere(self, subscriber: Subscriber) -> None:
        for s in self.subscribers.values():
            s.discard(subscriber)

    def unsubscribe_events(self, subscriber: Subscriber, *events) -> None:
        for e in events:
            self.subscribers[e].discard(subscriber)

    def notify(self, event, **kwargs) -> None:
        for s in self.subscribers[event]:
            s.update(event, **kwargs)
