def contains(iterable, *values):
    return all((v in iterable) for v in values)


def kebab2snake(s):
    return s.translate(str.maketrans("-", "_"))
