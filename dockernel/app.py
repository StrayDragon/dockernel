from rich import traceback

from .cli import main_arguments, run_subcommand

traceback.install(
    show_locals=True,
)


def run(argv: list) -> int:
    parsed_args = main_arguments.parse_args(argv[1:])
    return run_subcommand(parsed_args)
