# syntax=docker/dockerfile:1.6

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /opt/codegraphcontext

# Install system build dependencies required for Python packages like tree-sitter.
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        libffi-dev \
        libssl-dev \
        git \
    && rm -rf /var/lib/apt/lists/*

# Copy only the files required to install the package to leverage Docker layer caching.
COPY pyproject.toml README.md LICENSE MANIFEST.in ./
COPY src/ ./src/

# Install the CodeGraphContext package into the image.
RUN pip install --upgrade pip \
    && pip install --no-cache-dir .

# Drop privileges for runtime safety and create a writable workspace.
RUN useradd --create-home --shell /bin/bash cgc
USER cgc
WORKDIR /workspace

# Expose the CLI as the container entrypoint. Commands can be passed as arguments.
ENTRYPOINT ["cgc"]
CMD ["--help"]

