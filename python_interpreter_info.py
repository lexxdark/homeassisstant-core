import json
import os
import sys

import pkg_resources


def validate_path(path):
    if path:
        return path.split(os.pathsep)
    else:
        return None


def get_working_set():
    l = []
    for i in pkg_resources.working_set:
        l.append(f"{i.key} {i.version} {i.location}")
    return l


def get_version_info():
    return "{}.{}.{} {} serial={}".format(
        sys.version_info.major,
        sys.version_info.minor,
        sys.version_info.micro,
        sys.version_info.releaselevel,
        sys.version_info.serial,
    )


def main():
    d = {
        "general_info": {
            "sys.prefix": sys.prefix,
            "sys.executable": sys.executable,
            "sys.version_info": get_version_info(),
            "__file__": __file__ if "__file__" in globals() else None,
        },
        "sys.path": sys.path,
        "pkg_resources.working_set": get_working_set(),
        "environ": {
            "PATH": validate_path(os.getenv("PATH")),
            "PYTHONPATH": validate_path(os.getenv("PYTHONPATH")),
            "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV"),
            "CONDA_PREFIX": os.environ.get("CONDA_PREFIX"),
            "PYCHARM_HOSTED": os.environ.get("PYCHARM_HOSTED"),
        },
    }
    j = json.dumps(d, indent=4)
    print(j)


if __name__ == "__main__":
    main()
