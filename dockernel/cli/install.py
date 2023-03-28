from pathlib import Path
import platform
import docker
from typing import List
from argparse import Namespace
from .main import subparsers, set_subcommand_func
from ..kernelspec import (
    Kernelspec,
    InterruptMode,
    user_kernelspec_store,
    ensure_kernelspec_store_exists,
    kernelspec_dir,
    install_kernelspec,
)
import sys


arguments = subparsers.add_parser(
    __name__.split(".")[-1], help="Install dockerized kernel image into Jupyter.",
)
arguments.add_argument("image_name", help="Name of the docker image to use.",)
arguments.add_argument(
    "--name",
    help="Display name for the kernelspec. " "By default, container hostname is used.",
    default=None,
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
arguments.add_argument(
    "--kernels-path",
    help="kernels path to install, see https://jupyter-client.readthedocs.io/en/stable/kernels.html",
    default=f"{sys.prefix}/share/jupyter/kernels",
)


JUPYTER_CONNECTION_FILE_TEMPLATE = "{connection_file}"


def python_argv(system_type: str) -> List[str]:
    """Return proper command-line vector for python interpreter"""
    if system_type == "Linux" or system_type == "Darwin":
        argv = ["/usr/bin/env", "python", "-m"]
    elif system_type == "Windows":
        argv = ["python", "-m"]
    else:
        raise ValueError(f"unknown system type: {system_type}")
    return argv


def generate_kernelspec_argv(image_name: str, system_type: str) -> List[str]:
    dockernel_argv = [
        "dockernel",
        "start",
        image_name,
        JUPYTER_CONNECTION_FILE_TEMPLATE,
    ]
    return python_argv(system_type) + dockernel_argv


def image_digest(docker_client: docker.client.DockerClient, image_name: str) -> str:
    image = docker_client.images.get(image_name)
    return image.attrs["ContainerConfig"]["Hostname"]


def install(args: Namespace) -> int:
    system_type = platform.system()
    store_path = user_kernelspec_store(system_type)
    ensure_kernelspec_store_exists(store_path)

    argv = generate_kernelspec_argv(args.image_name, system_type)

    name = args.image_name if args.name is None else args.name
    if not name:
        raise ValueError("--image_name or --name must not empty")

    language = args.language
    if not language:
        raise ValueError("--language must not empty")

    kernelspec = Kernelspec(
        argv,
        name,
        language,
        interrupt_mode=InterruptMode.message,
    )

    kernels_path_str = args.kernels_path
    if not kernels_path_str:
        raise ValueError("--language must not empty")

    # docker_client = docker.from_env()
    # kernel_id = image_digest(docker_client, args.image_name)
    # location = kernelspec_dir(store_path, kernel_id)

    location = Path(kernels_path_str) / name
    install_kernelspec(location, kernelspec)
    # TODO: bare numbered exit statusses seem bad
    return 0


set_subcommand_func(parser=arguments, func=install)
