from typing import List
from .cli import main_arguments, run_subcommand
from rich import traceback
traceback.install(
    show_locals=True,
)


def run(argv: List) -> int:
    parsed_args = main_arguments.parse_args(argv[1:])
    return run_subcommand(parsed_args)
