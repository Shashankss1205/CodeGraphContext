# Docker Support

This repository now ships with a first-class Docker image so that the CLI can
run without requiring a local Python toolchain. The Dockerfile lives at the
repository root and installs the published package together with its
dependencies.

## Build the image locally

```bash
docker build -t codegraphcontext:latest .
```

To speed up builds in CI/CD you can take advantage of Docker layer caching. The
Dockerfile copies only the files required to install the package before running
`pip install .`, so subsequent builds after small source changes remain fast.

## Run CodeGraphContext via Docker

Run the CLI by mounting your project and the CodeGraphContext configuration
directory into the container:

```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  -v "$HOME/.codegraphcontext":/home/cgc/.codegraphcontext \
  codegraphcontext:latest setup
```

The image uses `cgc` as the entrypoint, so any subcommand can be passed
directly, for example:

```bash
docker run --rm -it \
  -v "$PWD":/workspace \
  -v "$HOME/.codegraphcontext":/home/cgc/.codegraphcontext \
  --env NEO4J_URI=bolt://neo4j:7687 \
  --env NEO4J_USERNAME=neo4j \
  --env NEO4J_PASSWORD=changeme \
  codegraphcontext:latest start
```

> **Note:** Mounting `~/.codegraphcontext` ensures that credentials saved by
> `cgc setup` persist across container runs. If you prefer managing
> credentials through environment variables, omit the volume and pass the
> variables with `--env` or `--env-file`.

## Publish to Docker Hub

1. Build the image with the package version tag:

   ```bash
   APP_VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
   docker build -t codegraphcontext:$APP_VERSION .
   ```

2. Tag the image for Docker Hub (replace `shashankss1205` with the Docker Hub
   namespace you own):

   ```bash
   docker tag codegraphcontext:$APP_VERSION shashankss1205/codegraphcontext:$APP_VERSION
   docker tag codegraphcontext:$APP_VERSION shashankss1205/codegraphcontext:latest
   ```

3. Authenticate and push:

   ```bash
   docker login
   docker push shashankss1205/codegraphcontext:$APP_VERSION
   docker push shashankss1205/codegraphcontext:latest
   ```

After the image has been published you can pull it directly:

```bash
docker pull shashankss1205/codegraphcontext:latest
docker run --rm -it shashankss1205/codegraphcontext:latest --help
```

