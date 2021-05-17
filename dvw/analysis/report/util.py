import os
from pathlib import Path


def contains(iterable, *values) -> bool:  # TODO: add typing
    return all((v in iterable) for v in values)


def kebab2snake(s: str) -> str:
    return s.translate(str.maketrans("-", "_"))


def create_path(*paths: str) -> str:
    path = os.path.join(*paths)
    Path(path).mkdir(parents=True, exist_ok=True)
    return path


def filename(path: str) -> str:
    return os.path.split(path)[1]


def path_join(*path: str) -> str:
    return os.path.join(*path)
