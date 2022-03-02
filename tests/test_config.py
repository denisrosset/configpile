from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Optional

import pytest
from typing_extensions import Annotated

import configpile
from configpile import types
from configpile.arg import HelpCmd, Param
from configpile.config import Config
from configpile.errors import Err


@dataclass(frozen=True)
class MyApp(Config):
    """
    This is a description
    """

    a: Annotated[int, Param.store(types.int_)]  #: Super doc message

    help_command: ClassVar[HelpCmd] = HelpCmd(short_flag_name="-h")  #: Displays help and exits


def test_construct() -> None:
    app = MyApp.parse_command_line_(args=[], env={})
