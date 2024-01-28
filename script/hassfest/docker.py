"""Generate and validate the dockerfile."""
from homeassistant import core
from homeassistant.util import executor, thread

from .model import Config, Integration

DOCKERFILE_TEMPLATE = r"""# Automatically generated by hassfest.
#
# To update, run python3 -m script.hassfest -p docker
ARG BUILD_FROM
FROM ${{BUILD_FROM}}

# Synchronize with homeassistant/core.py:async_stop
ENV \
    S6_SERVICES_GRACETIME={timeout}

ARG QEMU_CPU

WORKDIR /usr/src

## Setup Home Assistant Core dependencies
COPY requirements.txt homeassistant/
COPY homeassistant/package_constraints.txt homeassistant/homeassistant/
RUN \
    pip3 install \
        --only-binary=:all: \
        -r homeassistant/requirements.txt

COPY requirements_all.txt home_assistant_frontend-* home_assistant_intents-* homeassistant/
RUN \
    if ls homeassistant/home_assistant_frontend*.whl 1> /dev/null 2>&1; then \
        pip3 install homeassistant/home_assistant_frontend-*.whl; \
    fi \
    && if ls homeassistant/home_assistant_intents*.whl 1> /dev/null 2>&1; then \
        pip3 install homeassistant/home_assistant_intents-*.whl; \
    fi \
    && if [ "${{BUILD_ARCH}}" = "i386" ]; then \
        LD_PRELOAD="/usr/local/lib/libjemalloc.so.2" \
        MALLOC_CONF="background_thread:true,metadata_thp:auto,dirty_decay_ms:20000,muzzy_decay_ms:20000" \
        linux32 pip3 install \
            --only-binary=:all: \
            -r homeassistant/requirements_all.txt; \
    else \
        LD_PRELOAD="/usr/local/lib/libjemalloc.so.2" \
        MALLOC_CONF="background_thread:true,metadata_thp:auto,dirty_decay_ms:20000,muzzy_decay_ms:20000" \
        pip3 install \
            --only-binary=:all: \
            -r homeassistant/requirements_all.txt; \
    fi

## Setup Home Assistant Core
COPY . homeassistant/
RUN \
    pip3 install \
        --only-binary=:all: \
        -e ./homeassistant \
    && python3 -m compileall \
        homeassistant/homeassistant

# Home Assistant S6-Overlay
COPY rootfs /

WORKDIR /config
"""


def _generate_dockerfile() -> str:
    timeout = (
        core.STOPPING_STAGE_SHUTDOWN_TIMEOUT
        + core.STOP_STAGE_SHUTDOWN_TIMEOUT
        + core.FINAL_WRITE_STAGE_SHUTDOWN_TIMEOUT
        + core.CLOSE_STAGE_SHUTDOWN_TIMEOUT
        + executor.EXECUTOR_SHUTDOWN_TIMEOUT
        + thread.THREADING_SHUTDOWN_TIMEOUT
        + 10
    )
    return DOCKERFILE_TEMPLATE.format(timeout=timeout * 1000)


def validate(integrations: dict[str, Integration], config: Config) -> None:
    """Validate dockerfile."""
    dockerfile_content = _generate_dockerfile()
    config.cache["dockerfile"] = dockerfile_content

    dockerfile_path = config.root / "Dockerfile.main"
    if dockerfile_path.read_text() != dockerfile_content:
        config.add_error(
            "docker",
            "File Dockerfile.main is not up to date. Run python3 -m script.hassfest",
            fixable=True,
        )


def generate(integrations: dict[str, Integration], config: Config) -> None:
    """Generate dockerfile."""
    dockerfile_path = config.root / "Dockerfile.main"
    dockerfile_path.write_text(config.cache["dockerfile"])
