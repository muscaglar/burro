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
# No secret belongs in this file, in a build argument or in the image. The build
# reaches no store: a release is taken to the checkout before the image is built.

# Pinned by exact tag, not by digest. deploy/README.md says why, and how to pin one.
ARG PYTHON_IMAGE=python:3.13.15-slim-trixie

# The release this image serves, and the folder of the checkout it is taken from.
# With neither given the image carries the made-up city, as it is committed. A
# release of London is given by its id, from the folder the step `take` filled:
# deploy/README.md says how. The folder is named for the release, and the service
# refuses a folder whose name and manifest disagree.
ARG RELEASE_ID=syn-2026-09-23-01
ARG RELEASE_FROM=data/fixtures/synthetic

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


# What the image carries, held to what is committed. The made-up city is held to its
# own manifest. Any other release is carried only where its lock is committed under
# data/approved/, and every file of it has the hash and the size the lock gives: a
# file that differs, that is missing or that the lock does not name ends the build
# here. Nothing reaches the image from the checkout but through this stage. What
# was taken on a machine that writes a file for its owner alone is made readable
# to the user the service runs as.
FROM ${PYTHON_IMAGE} AS release

ARG RELEASE_ID
ARG RELEASE_FROM

COPY tools/public_log.py tools/release_lock.py /check/
COPY data/approved/ /check/approved/
COPY ${RELEASE_FROM}/ /srv/burro/release/
RUN python /check/release_lock.py carried /srv/burro/release "${RELEASE_ID}" \
        --approved /check/approved \
    && chmod -R a+rX /srv/burro/release


FROM ${PYTHON_IMAGE}

ARG RELEASE_ID

RUN groupadd --system --gid 10001 burro \
    && useradd --system --uid 10001 --gid 10001 --no-create-home \
        --shell /usr/sbin/nologin burro

COPY --from=build /opt/venv /opt/venv
COPY --from=release /srv/burro/release/ /srv/burro/release/

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
