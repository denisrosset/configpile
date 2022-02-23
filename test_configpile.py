from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import configpile
import configpile.app
from configpile.arg import Arg
from configpile.types import path, word


class FitsImportInventory(configpile.app.App):
    """
    RASSINE step that performs an inventory of observations
    """

    #: Relative path to the DACE CSV file
    dace_file: Arg[Optional[Path]] = Arg.store(path.empty_means_none(), default_value="")

    #: Instrument name if DACE file is not provided
    instrument: Arg[Optional[str]] = Arg.store(word.empty_means_none(), default_value="")

    #: Relative path to the folder containing input data files
    input_folder: Arg[Path] = Arg.store(path, default_value=None)

    #: Relative path of the output HDF5 information file
    info_file: Arg[Path] = Arg.store(path, default_value=None)


app: configpile.app.App = FitsImportInventory.app_()
c = app.parse_()
print(f"dace_file = {app.dace_file(c)}")
print(f"instrument = {app.instrument(c)}")
print(f"input_folder = {app.input_folder(c)}")
print(f"info_file = {app.info_file(c)}")
