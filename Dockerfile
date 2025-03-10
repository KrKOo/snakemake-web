FROM node:20-alpine as build

WORKDIR /app
ENV PATH=/app/node_modules/.bin:$PATH
ENV VITE_API_URL=/api

COPY ./web/package.json ./web/package-lock.json ./
RUN npm install

COPY ./web ./
RUN npm run build

FROM python:3.12

ARG PYTHON_VERSION=3.12

ENV FLASK_ENV=production
ENV MYUSER=myuser
ENV CONDA_DIR=/opt/conda
ENV PATH="${PATH}:${CONDA_DIR}/bin"
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt update && apt install -y rsync && rm -rf /var/lib/apt/lists/

RUN mkdir -p /app/api
COPY ./server/requirements.txt /app/api
RUN pip install -r /app/api/requirements.txt

# WORKDIR /tmp
# RUN wget --progress=dot:giga -O - \
#         "https://micro.mamba.pm/api/micromamba/linux-64/latest" | tar -xvj bin/micromamba && \
#     PYTHON_SPECIFIER="python=${PYTHON_VERSION}" && \
#     if [[ "${PYTHON_VERSION}" == "default" ]]; then PYTHON_SPECIFIER="python"; fi && \
#     # Install the packages
#     ./bin/micromamba install \
#         --root-prefix="${CONDA_DIR}" \
#         --prefix="${CONDA_DIR}" \
#         --yes \
#         "${PYTHON_SPECIFIER}" \
#         'mamba' -c conda-forge && \
#     rm -rf /tmp/bin/ && \
#     chmod -R 777 "${CONDA_DIR}"


# Install miniconda

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    /bin/bash /tmp/miniconda.sh -b -p $CONDA_DIR && \
    rm /tmp/miniconda.sh


RUN useradd -m $MYUSER
USER $MYUSER
RUN source ${CONDA_DIR}/etc/profile.d/conda.sh && conda init --all

COPY --from=build /app/dist /app/web
COPY ./server /app/api
WORKDIR /app/api
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "80", "--interface", "asgi3" , "--factory", "app:create_app"]
