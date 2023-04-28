import platform
import sys
from argparse import Namespace
from pathlib import Path
from typing import Union

import docker
import rich

from dockernel.cli.main import set_subcommand_func, subparsers
from dockernel.kernelspec import (
    InterruptMode,
    Kernelspec,
    ensure_kernelspec_store_exists,
    install_kernelspec,
    user_kernelspec_store,
)

arguments = subparsers.add_parser(
    __name__.split(".")[-1],
    help="Install dockerized kernel image into Jupyter.",
)
arguments.add_argument(
    "--image-name",
    help="Name of the docker image to use.",
    default="",
)
arguments.add_argument(
    "--list",
    help="show installed kernelspecs",
    action="store_true",
)
arguments.add_argument(
    "--name",
    help="Display name for the kernelspec. " "By default, container hostname is used.",
    default="",
)
arguments.add_argument(
    "--language",
    "-l",
    help="Language used by the kernel. "
    "Makes notebooks written in a given language "
    "run on different kernels, that use the same language, "
    "if this one is not found. "
    "By default, empty value is used.",
    default="",
)

DEFAULT_KERNELS_PATH = f"{sys.prefix}/share/jupyter/kernels"
arguments.add_argument(
    "--kernels-path",
    help=f"kernels path to install, now env is ' {DEFAULT_KERNELS_PATH} ', see https://jupyter-client.readthedocs.io/en/stable/kernels.html",  # noqa: E501
    default=DEFAULT_KERNELS_PATH,
)
arguments.add_argument(
    "--docker-volumes",
    help="same like docker run -v, e.g. '/home/xxx:/home/xxx,/home/a/b:/opt/a/b'",
    default="",
)
arguments.add_argument(
    "--force",
    help="force install",
    action="store_true",
)


JUPYTER_CONNECTION_FILE_TEMPLATE = "{connection_file}"


def python_argv(system_type: str) -> list[str]:
    """Return proper command-line vector for python interpreter"""
    if system_type in {"Linux", "Darwin"}:
        argv = ["/usr/bin/env", "python", "-m"]
    elif system_type == "Windows":
        argv = ["python", "-m"]
    else:
        raise ValueError(f"unknown system type: {system_type}")
    return argv


def _flatten(elems: list[Union[list[str], str]]) -> list[str]:
    res = []
    for elem in elems:
        if isinstance(elem, list):
            for e in elem:
                res.append(e)
        else:
            res.append(elem)
    return res


def generate_kernelspec_argv(
    image_name: str,
    system_type: str,
    docker_volumes: str = "",
) -> list[str]:
    opt_docker_volumes = []
    if docker_volumes:
        opt_docker_volumes = [
            "-v",
            docker_volumes,
        ]

    dockernel_argv = _flatten(
        [
            "dockernel",
            "start",
            opt_docker_volumes,
            image_name,
            JUPYTER_CONNECTION_FILE_TEMPLATE,
        ]
    )
    return python_argv(system_type) + dockernel_argv


def image_digest(docker_client: docker.client.DockerClient, image_name: str) -> str:
    image = docker_client.images.get(image_name)
    return image.attrs["ContainerConfig"]["Hostname"]


def _show_installed_kernelspecs_by_rich(kernels_path: Path) -> None:
    from rich.table import Table

    if kernels_path.exists() and kernels_path.is_dir():
        table = Table(title="kernelspec")

        table.add_column("Name", justify="left", style="magenta", no_wrap=True)
        table.add_column("Path", justify="left", style="green")

        for k in kernels_path.glob("*"):
            if not k.is_dir():
                continue
            table.add_row(k.name, str(k))
        rich.print(table)
    else:
        rich.print(f"[red]WARNING[/red]: kernelspec dir not exist? check ' {str(kernels_path)} '!")


def install(args: Namespace) -> int:
    kernels_path_str = args.kernels_path
    if not kernels_path_str:
        raise ValueError("--kernels-path must not empty")
    kernels_path = Path(kernels_path_str)

    if bool(args.list):
        _show_installed_kernelspecs_by_rich(kernels_path)
        return 0

    system_type = platform.system()
    store_path = user_kernelspec_store(system_type)
    ensure_kernelspec_store_exists(store_path)

    docker_volumes: str = args.docker_volumes
    if not docker_volumes:
        docker_volumes = ""

    image_name = str(args.image_name) if args.image_name and str(args.image_name).strip() else ""
    name = str(args.name if args.name and str(args.name).strip() else image_name).strip()
    if not name:
        raise ValueError("--image-name or --name must not empty")

    argv = generate_kernelspec_argv(
        image_name,
        system_type,
        docker_volumes=docker_volumes,
    )

    language = args.language
    if not language:
        raise ValueError("--language must not empty")

    kernelspec = Kernelspec(
        argv,
        name,
        language,
        interrupt_mode=InterruptMode.message,
    )

    force = bool(args.force)

    # docker_client = docker.from_env()
    # kernel_id = image_digest(docker_client, args.image_name)
    # location = kernelspec_dir(store_path, kernel_id)

    location = kernels_path / name
    install_kernelspec(location, kernelspec, force=force)
    # TODO: bare numbered exit statusses seem bad
    return 0


set_subcommand_func(parser=arguments, func=install)
