from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import configpile
import configpile.app
from configpile.arg import Param
from configpile.types import path, word


class FitsImportInventory(configpile.app.App):
    """
    RASSINE step that performs an inventory of observations
    """

    #: Relative path to the DACE CSV file
    dace_file: Param[Optional[Path]] = Param.store(path.empty_means_none(), default_value="")

    #: Instrument name if DACE file is not provided
    instrument: Param[Optional[str]] = Param.store(word.empty_means_none(), default_value="")

    #: Relative path to the folder containing input data files
    input_folder: Param[Path] = Param.store(path, default_value=None)

    #: Relative path of the output HDF5 information file
    info_file: Param[Path] = Param.store(path, default_value=None)


app = FitsImportInventory.app_()
c = app.parse_()
print(f"dace_file = {app.dace_file(c)}")
print(f"instrument = {app.instrument(c)}")
print(f"input_folder = {app.input_folder(c)}")
print(f"info_file = {app.info_file(c)}")
