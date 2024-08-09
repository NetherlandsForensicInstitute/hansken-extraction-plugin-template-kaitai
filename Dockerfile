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

FROM python:3.12 AS builder
ARG PIP_INDEX_URL=https://pypi.org/simple/
RUN apt-get -y update; apt-get -y install curl default-jre-headless unzip findutils && rm -rf /var/lib/apt/lists/*
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY requirements.txt /requirements.txt
RUN pip install -Ur /requirements.txt

COPY structs/* /structs/
RUN if [ "$(find ./structs/ -type f -name '*.ksy' | wc -l)" -ne 1 ]; then \
  (echo 'please put exactly one .ksy file in the struct-folder' && exit 1) ; fi
RUN curl -LO https://github.com/kaitai-io/kaitai_struct_compiler/releases/download/0.10/kaitai-struct-compiler-0.10.zip
RUN unzip kaitai-struct-compiler-0.10.zip
RUN cd structs && ../kaitai-struct-compiler-0.10/bin/kaitai-struct-compiler *.ksy -t python --python-package structs


###############################################################################
# Stage 2: create the distributable plugin image
# use a 'slim' image for running the actual plugin

FROM python:3.12-slim
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

COPY --from=builder /structs/ /app/structs/
COPY *.py /app/
WORKDIR /app
EXPOSE 8999
ENTRYPOINT ["serve_plugin", "-vv"]
CMD ["/app/plugin.py", "8999"]
