from pathlib import Path


def contains(iterable, *values) -> bool:  # TODO: add typing
    return all((v in iterable) for v in values)


def kebab2snake(s: str) -> str:
    return s.translate(str.maketrans("-", "_"))


def create_path(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)
