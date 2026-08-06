# flint2-ssh-api

REST API built with **FastAPI** for querying device connectivity status
on **GL.iNet FLINT2 (GL-MT6000)** routers via SSH.

## Features

- Check if a device is online (connected to Wi-Fi) by IP address
- Persistent SSH connection pool — no reconnect overhead per request
- TTL-based response cache — reduces router load
- Input validation, structured error responses
- Docker-ready

## Requirements

- Python 3.13+
- GL.iNet FLINT2 router with SSH enabled

## Starting server

Install dependencies
```shell
pip install uv
uv sync --extra dev
```

Copy env file
```shell
cp .env.example .env
```

Start server
```shell
uvicorn app.main:app --reload
```

## UnitTests

Run unit tests with pytest
```shell
pytest tests/ -v
```