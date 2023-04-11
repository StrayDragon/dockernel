from .install import arguments as install_arguments
from .main import arguments as main_arguments
from .main import run_subcommand, set_subcommand_func
from .start import arguments as start_arguments
from .uninstall import arguments as uninstall_arguments

__all__ = (
    "main_arguments",
    "install_arguments",
    "uninstall_arguments",
    "start_arguments",
    "set_subcommand_func",
    "run_subcommand",
)
