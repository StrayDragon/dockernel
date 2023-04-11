import shutil
import sys
from argparse import Namespace
from pathlib import Path

import rich

from dockernel.cli.main import set_subcommand_func, subparsers

arguments = subparsers.add_parser(
    __name__.split(".")[-1],
    help="Uninstall dockerized kernelspec",
)
arguments.add_argument(
    "--name",
    help="the installed image_name or --name value from install cmd",
)

DEFAULT_KERNELS_PATH = f"{sys.prefix}/share/jupyter/kernels"
arguments.add_argument(
    "--kernels-path",
    help=f"kernels path to install, now env is ' {DEFAULT_KERNELS_PATH} ', see https://jupyter-client.readthedocs.io/en/stable/kernels.html",  # noqa: E501
    default=DEFAULT_KERNELS_PATH,
)
arguments.add_argument(
    "--dry-run",
    help="not do actual operation, help for debug",
    action="store_true",
)


def uninstall(args: Namespace) -> int:
    name: str = args.name or ""
    if not name:
        raise ValueError("--name")

    kernels_path_str = args.kernels_path
    if not kernels_path_str:
        raise ValueError("--kernels-path must not empty")
    kernels_path = Path(kernels_path_str)
    if not all({kernels_path.exists(), kernels_path.is_dir()}):
        raise ValueError("--kernels-path not exist")

    is_dry_run = bool(args.dry_run)

    target_kernel_dir: Path = kernels_path / name
    if not all({target_kernel_dir.exists(), target_kernel_dir.is_dir()}):
        rich.print("[yellow]WARNING[/yellow]: not found target kernel config dir, do noting!")
    else:
        if is_dry_run:
            rich.print(f"[green]OK[/green]: ' {str(target_kernel_dir)} ' will be uninstalled (removed)")
        else:
            shutil.rmtree(target_kernel_dir)
            rich.print(f"[green]OK[/green]: ' {str(target_kernel_dir)} ' already uninstalled (removed)")

    return 0


set_subcommand_func(parser=arguments, func=uninstall)
