# Multi-stage Dockerfile, to build and package an extraction plugin
#  Recommended way to build the plugin is by calling tox:
#    tox -e package
#  if you need to pass a proxy:
#    tox -e package -- --build-arg https_proxy=https://your-proxy
#  if you want to pass a private Python package index:
#     tox -e package -- --build-arg PIP_INDEX_URL=https://your-pypi-mirror

###############################################################################
# Stage 1: build the plugin
# use a 'fat' image to setup the dependencies we'll need

FROM debian:bookworm AS builder
ARG PIP_INDEX_URL=https://pypi.org/simple/
# build wheels for all dependencies in /app/dist
RUN mkdir --parents /app/dist
RUN apt-get -y update; apt-get -y install curl default-jre unzip pip
COPY requirements.txt /app/requirements.txt
RUN pip wheel --requirement /app/requirements.txt --wheel-dir /app/dist
RUN apt-get -y install findutils
RUN mkdir --parents /structs
COPY structs/* /structs/
RUN if [ "$(find ./structs/ -type f -name '*.ksy' | wc -l)" -ne 1 ]; then exit 1 ; fi
RUN curl -LO https://github.com/kaitai-io/kaitai_struct_compiler/releases/download/0.10/kaitai-struct-compiler-0.10.zip
RUN unzip kaitai-struct-compiler-0.10.zip
RUN cd structs && ../kaitai-struct-compiler-0.10/bin/kaitai-struct-compiler *.ksy -t python --python-package structs

###############################################################################
# Stage 2: create the distributable plugin image
# use a 'slim' image for running the actual plugin

FROM python:3.11-slim
RUN mkdir --parents /app/dist
COPY --from=builder /app/dist/*.whl /app/dist/
COPY --from=builder /structs/ /app/structs/
RUN pip install --no-index /app/dist/*.whl
COPY *.py /app/
EXPOSE 8999
ENTRYPOINT ["/usr/local/bin/serve_plugin", "-vv"]
CMD ["/app/plugin.py", "8999"]
