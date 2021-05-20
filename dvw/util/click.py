from enum import Enum
from typing import List, Any, Optional, Callable, Type

import click
from click import Context, Parameter, Option, Group

from .util import enum_values


class TransparentGroup(Group):
    def parse_args(self, ctx: Context, args: List[str]) -> List[str]:
        self._pass_params_to_commands()
        return super().parse_args(ctx, args)

    def _pass_params_to_commands(self) -> None:
        for c in self.commands.values():
            params = list(self.params)
            params.extend(c.params)
            c.params = params
        self.params = []


class EnumType(click.Choice):
    def __init__(
        self,
        enum: Type[Enum],
        type_fn: Optional[Callable[[Any], Any]] = None,
        by_name: bool = False,
    ) -> None:
        choices = list(enum.__members__) if by_name else enum_values(enum)
        choices = list(map(str, choices))
        super().__init__(choices)
        self.enum = enum
        self.type_fn = type_fn
        self.by_name = by_name

    def convert(
        self, value, param: Optional[Parameter], ctx: Optional[Context]
    ) -> Enum:
        enum_value = super().convert(value, param, ctx)
        if self.type_fn:
            enum_value = self.type_fn(enum_value)
        if self.by_name:
            return self.enum[enum_value]
        return self.enum(enum_value)


def append_flag(option, type_):
    def callback(ctx: Context, param: Parameter, value):
        if value:
            const = ctx.params.setdefault(option, [])
            const.append(type_(param.name))
        return value

    return callback


def update_context(ctx: Context, **kwargs) -> None:
    ctx.ensure_object(dict)
    ctx.obj.update(kwargs)


def add_options(options: List[Type[Option]]) -> Callable:
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options
