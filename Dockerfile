# We need gcc to install aiohttp, so we can't use slim
FROM python:3.9-bullseye

# Copy the app
COPY app /app

# Use pip as the build frontend
COPY requirements.txt /app
RUN python -m pip install -r /app/requirements.txt

# For web app:
EXPOSE 8080/tcp

LABEL version="v1.0.0-beta.1"

# Reference:
# https://blueos.cloud/docs/blueos/1.2/development/extensions
# https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerCreate
LABEL permissions='\
{\
  "ExposedPorts": {\
    "8080/tcp": {},\
  },\
  "HostConfig": {\
    "ExtraHosts": ["host.docker.internal:host-gateway"],\
    "PortBindings": {\
      "8080/tcp": [\
        {\
          "HostPort": ""\
        }\
      ]\
    }\
  },\
  "Env": [\
    "MAVLINK2REST_URL=http://host.docker.internal/mavlink2rest/v1",\
  ],\
}'
LABEL authors='[\
    {\
        "name": "Clyde McQueen",\
        "email": "clyde@mcqueen.net"\
    }\
]'
LABEL company='{\
        "about": "",\
        "name": "Discovery Bay",\
        "email": "clyde@mcqueen.net"\
    }'
LABEL type="tool"
LABEL tags='[\
    "surftrak",\
]'
LABEL readme='https://raw.githubusercontent.com/clydemcqueen/surftrak_fixit/{tag}/README.md'
LABEL links='{\
    "website": "https://github.com/clydemcqueen/surftrak_fixit",\
    "support": "https://github.com/clydemcqueen/surftrak_fixit/issues"\
}'
LABEL requirements="core >= 1.1"

ENTRYPOINT cd /app && python main.py --mavlink2rest_url $MAVLINK2REST_URL
