import click

from .util import enum_values


class IgnoreRequiredWithHelp(click.Group):
    def parse_args(self, ctx, args):
        is_help = any(h in args for h in ctx.help_option_names)
        if is_help:
            for param in self.params:
                param.required = False
        return super().parse_args(ctx, args)


class EnumType(click.Choice):
    def __init__(self, enum, type_fn=None, by_name=False):
        choices = list(enum.__members__) if by_name else enum_values(enum)
        choices = list(map(str, choices))
        super().__init__(choices)
        self.enum = enum
        self.type_fn = type_fn
        self.by_name = by_name

    def convert(self, value, param, ctx):
        enum_value = super().convert(value, param, ctx)
        if self.type_fn:
            enum_value = self.type_fn(enum_value)
        if self.by_name:
            return self.enum[enum_value]
        return self.enum(enum_value)


def append_const(option, type_):
    def callback(ctx, param, value):
        if value:
            const = ctx.params.setdefault(option, [])
            const.append(type_(value))
        return value

    return callback


def update_context(ctx, **kwargs):
    ctx.ensure_object(dict)
    ctx.obj.update(kwargs)


def default_help_context():
    return {"help_option_names": ["-h", "--help"]}


def add_click_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options
