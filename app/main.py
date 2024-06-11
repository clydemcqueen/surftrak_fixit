#! /usr/bin/env python3
import argparse
import asyncio
from typing import Any

import fastapi
import fastapi.staticfiles
import uvicorn
from loguru import logger

import mav_client
import surftrak_status


def main(args):
    # Create a mav object
    logger.info(f'mavlink2rest URL: {args.mavlink2rest_url}')
    mav = mav_client.MavClient(args.mavlink2rest_url)

    # Create status object
    status = surftrak_status.SurftrakStatus(mav)

    # Create a FastAPI app
    app = fastapi.FastAPI(title='Surftrak Fixit', description='Diagnose and fix surftrak problems')

    # Add a FastAPI route: /status returns a dictionary
    # Pydantic barks if I use "<built-in function any>", so stick with typing.Any
    @app.get("/status", status_code=fastapi.status.HTTP_200_OK)
    async def get_status() -> Any:
        return status.get_status()

    # Create a FastAPI sub-application: serve static files in /app/static
    # This must come after more specific routes, e.g., /status
    app.mount("/", fastapi.staticfiles.StaticFiles(directory="static", html=True), name="static")

    # Add a FastAPI route: / returns index.html
    # Return index.html
    @app.get("/", response_class=fastapi.responses.FileResponse)
    async def root() -> Any:
        return "index.html"

    # Create an async event loop, we'll use it for both the websocket connection and the uvicorn web server
    loop = asyncio.new_event_loop()

    # Set the event loop for the current thread, allows for a cleaner shutdown (somehow)
    asyncio.set_event_loop(loop)

    # Create a websocket connection to mavlink2rest and keep it open
    # Add this as a task on our event loop
    loop.create_task(mav.open_websocket())

    # Start a web server
    # Uvicorn will add the server as a task on our event loop when we call serve()
    # Run with logging disabled, we'll use loguru to log interesting things
    logger.info('starting web server, press Ctrl-C to stop')
    config = uvicorn.Config(app, port=8080, loop=loop, log_config=None)
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())


if __name__ == "__main__":
    # Running as extension:        http://host.docker.internal/mavlink2rest/v1
    # Debugging from topside:      http://192.168.2.2/mavlink2rest/v1

    logger.info(f"starting surftrak_fixit")
    parser = argparse.ArgumentParser()
    parser.add_argument('--mavlink2rest_url', type=str,
                        default='http://host.docker.internal/mavlink2rest/v1',
                        help='mavlink2rest URL')
    main(parser.parse_args())
