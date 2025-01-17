import json
from argparse import Namespace
from pathlib import Path

import docker

from .main import set_subcommand_func, subparsers

arguments = subparsers.add_parser(__name__.split(".")[-1], help="Start a dockernel.")

# TODO: add a note about how to pull / build an image
# TODO: add a note about default images
arguments.add_argument("image_name", help="Name of the docker image to use.")

# TODO: make this one optional
# TODO: add a help note about it being put into environment variables
# TODO: add a note about how some kernels react when it is not given
arguments.add_argument("connection_file", help="The connection file to use.")

arguments.add_argument(
    "-v",
    help="same like docker run -v, e.g. '/home/xxx:/home/xxx,/home/a/b:/opt/a/b'",
    default="",
)


CONTAINER_CONNECTION_SPEC_PATH = "/kernel-connection-spec.json"
CONTAINER_CONNECTION_SPEC_ENV_VAR = "DOCKERNEL_CONNECTION_FILE"


def set_connection_ip(connection_file: Path, ip: str = "0.0.0.0") -> dict:
    """Set/update ip field in connection file"""

    connection = json.loads(connection_file.read_text())
    connection["ip"] = ip
    connection_file.write_text(json.dumps(connection))

    return connection


def start(parsed_args: Namespace) -> int:
    containers = docker.from_env().containers
    image_name = parsed_args.image_name
    connection_file = Path(parsed_args.connection_file)

    volumes = []
    if v_map := parsed_args.v:
        if isinstance(v_map, str):
            volumes = v_map.split(",")

    connection = set_connection_ip(connection_file, "0.0.0.0")
    port_mapping = {connection[k]: connection[k] for k in connection if "_port" in k}

    # TODO: parametrize connection spec file bind path
    connection_file_mount = docker.types.Mount(
        target=CONTAINER_CONNECTION_SPEC_PATH,
        source=str(connection_file.absolute()),
        type="bind",
        # XXX: some kernels still open connection spec in write mode
        # (I'm looking at you, IPython), even though it's not being written
        # into.
        read_only=False,
    )

    env_vars = {CONTAINER_CONNECTION_SPEC_ENV_VAR: CONTAINER_CONNECTION_SPEC_PATH}

    # TODO: parametrize possible mounts
    # TODO: log stdout and stderr
    # TODO: use detached=True?
    # TODO(@l8ng): add volumn mapping host and container
    containers.run(
        image_name,
        auto_remove=True,
        environment=env_vars,
        mounts=[connection_file_mount],
        network_mode="bridge",
        ports=port_mapping,
        stdout=True,
        stderr=True,
        volumes=volumes,
    )

    # TODO: bare numbered exit statusses seem bad
    return 0


set_subcommand_func(parser=arguments, func=start)
