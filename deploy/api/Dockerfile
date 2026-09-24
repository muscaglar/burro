# Burro's API: FastAPI over one data release held in memory. No database.
#
# Build from the repository root, because the image takes files from three folders:
#
#   docker build --file deploy/api/Dockerfile --tag burro-api .
#
# deploy/api/Dockerfile.dockerignore says what may enter the build.
# deploy/README.md says how the image reaches Fly.io.
#
# `make public-only` reads this file and fails on any URL whose host is not on
# its public list. A local address counts. Write no URL here.
#
# No secret belongs in this file, in a build argument or in the image.

# Pinned by exact tag, not by digest. deploy/README.md says why, and how to pin one.
ARG PYTHON_IMAGE=python:3.13.15-slim-trixie

FROM ${PYTHON_IMAGE} AS build

RUN python -m venv /opt/venv

WORKDIR /src
COPY packages/core packages/core
COPY services/api services/api

# No lockfile is committed yet, so the version ranges in each pyproject.toml are
# the only pin, and two builds a week apart can differ. Packages come from pip's
# own default, the public index: none is named here. See docs/adr/0008.
# Both folders are named so that the API's dependency on core is met from this
# checkout and never from an index.
RUN /opt/venv/bin/pip install --no-cache-dir --disable-pip-version-check \
        ./packages/core ./services/api


FROM ${PYTHON_IMAGE}

# The release this image serves. The folder is named for the release, and the
# service refuses a folder whose name and manifest disagree.
ARG RELEASE_ID=syn-2026-09-23-01

RUN groupadd --system --gid 10001 burro \
    && useradd --system --uid 10001 --gid 10001 --no-create-home \
        --shell /usr/sbin/nologin burro

COPY --from=build /opt/venv /opt/venv
COPY data/fixtures/synthetic/${RELEASE_ID}/ /srv/burro/release/${RELEASE_ID}/

# BURRO_RELEASE_DIR must be set: once the package is installed, its default
# points at a checkout that is not there.
# BURRO_HOST is every address inside the container, because the host's proxy
# reaches the service from outside it. Nothing else can: only the port below is
# published, and deploy/api/fly.toml puts TLS in front of it.
# BURRO_ALLOWED_ORIGINS is not set here. It belongs to a deployment, not to the
# image, and with none set only a page on the visitor's own machine is answered.
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BURRO_RELEASE_DIR=/srv/burro/release/${RELEASE_ID} \
    BURRO_HOST=0.0.0.0 \
    BURRO_PORT=8080

USER 10001:10001
WORKDIR /srv/burro
EXPOSE 8080

# Fly.io ignores this and runs the check in fly.toml. It is here for `docker run`
# and for CI. It asks the service itself, over the loopback address, and passes
# only on a 200.
HEALTHCHECK --interval=15s --timeout=3s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import http.client, os, sys; c = http.client.HTTPConnection('127.0.0.1', int(os.environ['BURRO_PORT']), timeout=2); c.request('GET', '/healthz'); sys.exit(c.getresponse().status != 200)"]

CMD ["burro-api", "serve"]
