# We need gcc to install aiohttp, so we can't use slim
FROM python:3.9-bullseye

# Copy and run setup.py
COPY app/setup.py /app/setup.py
RUN python /app/setup.py install

# Copy the app
COPY app /app

# For web app:
EXPOSE 8080/tcp

LABEL version="v0.0.1"

# Reference:
# https://docs.bluerobotics.com/ardusub-zola/software/onboard/BlueOS-1.1/development/extensions/
# https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerCreate
LABEL permissions='\
{\
  "ExposedPorts": {\
    "8080/tcp": {},\
  },\
  "HostConfig": {\
    "PortBindings": {\
      "8080/tcp": [\
        {\
          "HostPort": ""\
        }\
      ]\
    }\
  },\
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

ENTRYPOINT cd /app && python main.py
